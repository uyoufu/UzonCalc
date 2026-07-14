use std::{
    fs::{self, OpenOptions},
    net::{SocketAddr, TcpStream},
    path::{Path, PathBuf},
    process::{Child, Command, Stdio},
    sync::Mutex,
    thread,
    time::{Duration, Instant},
};

const API_HOST: &str = "127.0.0.1";
const API_PORT: u16 = 3345;
const API_CONNECT_TIMEOUT: Duration = Duration::from_millis(300);
const API_READY_TIMEOUT: Duration = Duration::from_secs(60);
const API_READY_POLL_INTERVAL: Duration = Duration::from_millis(300);

pub struct ApiProcessState {
    child: Mutex<Option<Child>>,
}

pub struct ApiStartupResult {
    pub state: ApiProcessState,
    pub error_message: Option<String>,
}

struct StartApiProcessResult {
    child: Option<Child>,
    error_message: Option<String>,
}

impl ApiProcessState {
    pub fn try_start() -> ApiStartupResult {
        let result = start_api_process();

        ApiStartupResult {
            state: Self {
                child: Mutex::new(result.child),
            },
            error_message: result.error_message,
        }
    }

    pub fn stop(&self) {
        let Ok(mut child_guard) = self.child.lock() else {
            log::error!("failed to lock api process state while stopping");
            return;
        };

        let Some(mut child) = child_guard.take() else {
            return;
        };

        match child.try_wait() {
            Ok(Some(status)) => {
                log::info!("api process already exited with status: {status}");
                return;
            }
            Ok(None) => {}
            Err(error) => {
                log::warn!("failed to query api process status: {error}");
            }
        }

        if let Err(error) = child.kill() {
            log::warn!("failed to stop api process: {error}");
        } else {
            log::info!("sent kill signal to api process");
        }

        match child.wait() {
            Ok(status) => log::info!("api process exited with status: {status}"),
            Err(error) => log::warn!("failed to wait for api process exit: {error}"),
        }
    }
}

impl Drop for ApiProcessState {
    fn drop(&mut self) {
        self.stop();
    }
}

fn start_api_process() -> StartApiProcessResult {
    log::info!("checking api service on {API_HOST}:{API_PORT}");

    if is_api_running() {
        log::info!("api is already running on {API_HOST}:{API_PORT}");
        return StartApiProcessResult {
            child: None,
            error_message: None,
        };
    }

    let exe_dir = match current_exe_dir() {
        Some(exe_dir) => exe_dir,
        None => {
            return StartApiProcessResult {
                child: None,
                error_message: Some("Failed to resolve current executable directory.".to_string()),
            };
        }
    };
    let python_exe = exe_dir
        .join("dist")
        .join("python-embedded")
        .join("python.exe");
    let main_py = exe_dir.join("main.py");
    let log_dir = exe_dir.join("logs");

    if !python_exe.is_file() {
        let message = format!("Python executable is missing: {}", python_exe.display());
        log::warn!("{message}");
        return StartApiProcessResult {
            child: None,
            error_message: Some(message),
        };
    }

    if !main_py.is_file() {
        let message = format!("Backend entry file is missing: {}", main_py.display());
        log::warn!("{message}");
        return StartApiProcessResult {
            child: None,
            error_message: Some(message),
        };
    }

    if let Err(error) = fs::create_dir_all(&log_dir) {
        log::warn!(
            "failed to create api diagnostic log directory {}: {error}",
            log_dir.display()
        );
    }

    let stdout = open_process_log(&log_dir.join("tauri-api.stdout.log"), "stdout");
    let stderr = open_process_log(&log_dir.join("tauri-api.stderr.log"), "stderr");

    log::info!(
        "starting api process: python={}, main={}, working_dir={}, target=http://{API_HOST}:{API_PORT}",
        python_exe.display(),
        main_py.display(),
        exe_dir.display()
    );

    let mut command = Command::new(&python_exe);
    command
        .arg(&main_py)
        .current_dir(&exe_dir)
        .stdin(Stdio::null());

    match stdout {
        Some(stdout) => {
            command.stdout(Stdio::from(stdout));
        }
        None => {
            command.stdout(Stdio::null());
        }
    }

    match stderr {
        Some(stderr) => {
            command.stderr(Stdio::from(stderr));
        }
        None => {
            command.stderr(Stdio::null());
        }
    }

    configure_background_process(&mut command);

    match command.spawn() {
        Ok(mut child) => {
            log::info!(
                "started api process from {}, pid={}",
                python_exe.display(),
                child.id()
            );
            match wait_for_api_ready(&mut child) {
                Ok(()) => StartApiProcessResult {
                    child: Some(child),
                    error_message: None,
                },
                Err(error_message) => StartApiProcessResult {
                    child: Some(child),
                    error_message: Some(error_message),
                },
            }
        }
        Err(error) => {
            let message = format!(
                "failed to start api process from {}: {error}",
                python_exe.display()
            );
            log::warn!("{message}");
            StartApiProcessResult {
                child: None,
                error_message: Some(message),
            }
        }
    }
}

fn wait_for_api_ready(child: &mut Child) -> Result<(), String> {
    let started_at = Instant::now();

    while started_at.elapsed() < API_READY_TIMEOUT {
        match child.try_wait() {
            Ok(Some(status)) => {
                let message = format!("API process exited before becoming ready: {status}");
                log::warn!("{message}");
                return Err(message);
            }
            Ok(None) => {}
            Err(error) => {
                let message =
                    format!("Failed to query API process during readiness check: {error}");
                log::warn!("{message}");
                return Err(message);
            }
        }

        if is_api_running() {
            log::info!(
                "api service is listening on {API_HOST}:{API_PORT} after {:?}",
                started_at.elapsed()
            );
            return Ok(());
        }

        thread::sleep(API_READY_POLL_INTERVAL);
    }

    let message = format!(
        "api service did not listen on {API_HOST}:{API_PORT} within {:?}; process is still tracked for shutdown",
        API_READY_TIMEOUT
    );
    log::warn!("{message}");
    Err(message)
}

fn is_api_running() -> bool {
    let address = SocketAddr::from(([127, 0, 0, 1], API_PORT));
    TcpStream::connect_timeout(&address, API_CONNECT_TIMEOUT).is_ok()
}

fn open_process_log(path: &Path, name: &str) -> Option<fs::File> {
    match OpenOptions::new().create(true).append(true).open(path) {
        Ok(file) => Some(file),
        Err(error) => {
            log::warn!(
                "failed to open api {name} diagnostic log {}: {error}",
                path.display()
            );
            None
        }
    }
}

fn current_exe_dir() -> Option<PathBuf> {
    match std::env::current_exe() {
        Ok(exe_path) => exe_path.parent().map(Path::to_path_buf),
        Err(error) => {
            log::warn!("failed to resolve current executable path: {error}");
            None
        }
    }
}

#[cfg(windows)]
fn configure_background_process(command: &mut Command) {
    use std::os::windows::process::CommandExt;

    const CREATE_NO_WINDOW: u32 = 0x08000000;
    command.creation_flags(CREATE_NO_WINDOW);
}

#[cfg(not(windows))]
fn configure_background_process(_command: &mut Command) {}
