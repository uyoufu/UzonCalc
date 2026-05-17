use std::{
    net::{SocketAddr, TcpStream},
    path::{Path, PathBuf},
    process::{Child, Command, Stdio},
    sync::Mutex,
    time::Duration,
};

const API_HOST: &str = "127.0.0.1";
const API_PORT: u16 = 3346;
const API_CONNECT_TIMEOUT: Duration = Duration::from_millis(300);

pub struct ApiProcessState {
    child: Mutex<Option<Child>>,
}

impl ApiProcessState {
    pub fn try_start() -> Self {
        Self {
            child: Mutex::new(start_api_process()),
        }
    }

    fn stop(&self) {
        let Ok(mut child_guard) = self.child.lock() else {
            log::error!("failed to lock api process state while stopping");
            return;
        };

        let Some(mut child) = child_guard.take() else {
            return;
        };

        match child.try_wait() {
            Ok(Some(_status)) => return,
            Ok(None) => {}
            Err(error) => {
                log::warn!("failed to query api process status: {error}");
            }
        }

        if let Err(error) = child.kill() {
            log::warn!("failed to stop api process: {error}");
        }

        if let Err(error) = child.wait() {
            log::warn!("failed to wait for api process exit: {error}");
        }
    }
}

impl Drop for ApiProcessState {
    fn drop(&mut self) {
        self.stop();
    }
}

fn start_api_process() -> Option<Child> {
    if is_api_running() {
        log::info!("api is already running on {API_HOST}:{API_PORT}");
        return None;
    }

    let exe_dir = match current_exe_dir() {
        Some(exe_dir) => exe_dir,
        None => return None,
    };
    let python_exe = exe_dir
        .join("dist")
        .join("python-embedded")
        .join("python.exe");
    let main_py = exe_dir.join("main.py");

    if !python_exe.is_file() {
        log::info!(
            "skip api startup because python executable is missing: {}",
            python_exe.display()
        );
        return None;
    }

    if !main_py.is_file() {
        log::info!(
            "skip api startup because main.py is missing: {}",
            main_py.display()
        );
        return None;
    }

    let mut command = Command::new(&python_exe);
    command
        .args([
            "-m",
            "uvicorn",
            "main:app",
            "--host",
            API_HOST,
            "--port",
            &API_PORT.to_string(),
            "--log-level",
            "info",
        ])
        .current_dir(&exe_dir)
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null());

    configure_background_process(&mut command);

    match command.spawn() {
        Ok(child) => {
            log::info!("started api process from {}", python_exe.display());
            Some(child)
        }
        Err(error) => {
            log::warn!(
                "failed to start api process from {}: {error}",
                python_exe.display()
            );
            None
        }
    }
}

fn is_api_running() -> bool {
    let address = SocketAddr::from(([127, 0, 0, 1], API_PORT));
    TcpStream::connect_timeout(&address, API_CONNECT_TIMEOUT).is_ok()
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
