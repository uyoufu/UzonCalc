#[macro_use]
extern crate rust_i18n;

pub mod api_process;
pub mod config;
pub mod locale;
pub mod server;
pub mod tray;

use api_process::ApiProcessState;
use config::{app_config_paths, load_app_config, AppConfig};
use locale::{app_title, set_current_locale, startup_loading_text};
use server::{spawn_language_server, SharedState};
use std::{
    error::Error,
    path::PathBuf,
    thread,
    time::{Duration, Instant},
};
use tauri::{AppHandle, Manager, WebviewUrl, WebviewWindow, WebviewWindowBuilder};

rust_i18n::i18n!("locales");

const MAIN_WINDOW_LABEL: &str = "main";
const WELCOME_WINDOW_LABEL: &str = "welcome";
const WELCOME_MIN_DISPLAY_DURATION: Duration = Duration::from_secs(1);

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    set_current_locale(locale::AppLocale::ZhCn);

    let mut builder = tauri::Builder::default();

    #[cfg(desktop)]
    {
        builder = builder.plugin(tauri_plugin_single_instance::init(|app, _args, _cwd| {
            restore_existing_instance(app);
        }));
    }

    builder
        .setup(|app| {
            app.handle().plugin(
                tauri_plugin_log::Builder::default()
                    .level(log::LevelFilter::Info)
                    .build(),
            )?;

            log::info!("tauri setup started");
            let app_config = load_app_config(app);
            log::info!("app config loaded");
            set_current_locale(app_config.locale());

            let welcome_window = create_welcome_window(app)?;
            let welcome_started_at = Instant::now();
            log::info!("welcome window created: {}", welcome_window.label());

            let main_window = create_main_window(app, &app_config)?;
            log::info!("main window created: {}", main_window.label());

            let tray_state = tray::setup_tray(app, &main_window)?;
            log::info!("tray initialized");
            let shared_state = SharedState::new(
                app.handle().clone(),
                app_config_paths(app),
                app_config,
                main_window.label().to_string(),
                tray_state,
            );
            app.manage(shared_state.clone());
            log::info!("starting language service");
            spawn_language_server(shared_state);
            start_api_and_finish_welcome(
                app.handle().clone(),
                welcome_window,
                main_window,
                welcome_started_at,
            );
            log::info!("tauri setup completed");

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

fn restore_existing_instance(app: &AppHandle) {
    if let Some(window) = app
        .get_webview_window(MAIN_WINDOW_LABEL)
        .or_else(|| app.webview_windows().into_values().next())
    {
        if let Err(error) = window.show() {
            log::error!("failed to show existing window: {error}");
        }

        if let Err(error) = window.unminimize() {
            log::debug!("failed to unminimize existing window: {error}");
        }

        if let Err(error) = window.set_focus() {
            log::error!("failed to focus existing window: {error}");
        }
    }
}

fn create_welcome_window(app: &mut tauri::App) -> Result<WebviewWindow, Box<dyn Error>> {
    let window = WebviewWindowBuilder::new(
        app.handle(),
        WELCOME_WINDOW_LABEL,
        WebviewUrl::App(PathBuf::from("welcome.html")),
    )
    .title(app_title())
    .inner_size(720.0, 420.0)
    .resizable(false)
    .maximizable(false)
    .minimizable(false)
    .decorations(false)
    .center()
    .initialization_script(welcome_initialization_script()?)
    .build()?;

    Ok(window)
}

fn welcome_initialization_script() -> Result<String, serde_json::Error> {
    let loading_text = serde_json::to_string(&startup_loading_text())?;
    Ok(format!(
        "window.__UZON_WELCOME_LOADING_TEXT__ = {loading_text};"
    ))
}

fn create_main_window(
    app: &mut tauri::App,
    app_config: &AppConfig,
) -> Result<WebviewWindow, Box<dyn Error>> {
    let mut window_config = app
        .config()
        .app
        .windows
        .first()
        .cloned()
        .ok_or_else(|| missing_main_window_error())?;

    if let Some(url) = app_config.webview_url() {
        window_config.url = url;
    }

    window_config.title = app_title();

    let window = WebviewWindowBuilder::from_config(app.handle(), &window_config)?
        .visible(false)
        .build()?;
    Ok(window)
}

fn start_api_and_finish_welcome(
    app_handle: AppHandle,
    welcome_window: WebviewWindow,
    main_window: WebviewWindow,
    welcome_started_at: Instant,
) {
    thread::spawn(move || {
        log::info!("starting api process state");
        app_handle.manage(ApiProcessState::try_start());
        finish_welcome(welcome_window, main_window, welcome_started_at);
    });
}

fn finish_welcome(
    welcome_window: WebviewWindow,
    main_window: WebviewWindow,
    welcome_started_at: Instant,
) {
    if let Some(remaining) = WELCOME_MIN_DISPLAY_DURATION.checked_sub(welcome_started_at.elapsed())
    {
        thread::sleep(remaining);
    }

    if let Err(error) = welcome_window.close() {
        log::warn!("failed to close welcome window: {error}");
    }

    if let Err(error) = main_window.show() {
        log::error!("failed to show main window: {error}");
    }

    if let Err(error) = main_window.set_focus() {
        log::debug!("failed to focus main window: {error}");
    }
}

fn missing_main_window_error() -> std::io::Error {
    std::io::Error::new(
        std::io::ErrorKind::InvalidData,
        "missing main window configuration",
    )
}
