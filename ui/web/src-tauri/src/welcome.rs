use crate::{
    api_process::ApiProcessState,
    locale::{app_title, launch_error_texts, welcome_texts},
};
use std::{
    error::Error,
    path::PathBuf,
    thread,
    time::{Duration, Instant},
};
use tauri::{AppHandle, Manager, WebviewUrl, WebviewWindow, WebviewWindowBuilder};

const WELCOME_WINDOW_LABEL: &str = "welcome";
const WELCOME_MIN_DISPLAY_DURATION: Duration = Duration::from_secs(1);

pub fn create_welcome_window(app: &mut tauri::App) -> Result<WebviewWindow, Box<dyn Error>> {
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
    let welcome_texts = serde_json::to_string(&welcome_texts())?;
    let launch_error_texts = serde_json::to_string(&launch_error_texts())?;

    Ok(format!(
        "window.__UZON_WELCOME_TEXTS__ = {welcome_texts};window.__UZON_LAUNCH_ERROR_TEXTS__ = {launch_error_texts};"
    ))
}

pub fn start_api_and_finish_welcome(
    app_handle: AppHandle,
    welcome_window: WebviewWindow,
    main_window: WebviewWindow,
    welcome_started_at: Instant,
) {
    thread::spawn(move || {
        log::info!("starting api process state");
        let startup_result = ApiProcessState::try_start();
        let error_message = startup_result.error_message.clone();
        app_handle.manage(startup_result.state);
        finish_welcome(
            welcome_window,
            main_window,
            welcome_started_at,
            error_message,
        );
    });
}

fn finish_welcome(
    welcome_window: WebviewWindow,
    main_window: WebviewWindow,
    welcome_started_at: Instant,
    error_message: Option<String>,
) {
    if let Some(remaining) = WELCOME_MIN_DISPLAY_DURATION.checked_sub(welcome_started_at.elapsed())
    {
        thread::sleep(remaining);
    }

    if let Some(error_message) = error_message {
        show_launch_error(welcome_window, error_message);
        return;
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

fn show_launch_error(welcome_window: WebviewWindow, error_message: String) {
    log::warn!("showing launch error page: {error_message}");

    let message_json = serde_json::to_string(&error_message).unwrap_or_else(|error| {
        log::warn!("failed to serialize launch error message: {error}");
        "\"\"".to_string()
    });
    let script = format!(
        "window.location.replace('launch-error.html?message=' + encodeURIComponent({message_json}));"
    );

    if let Err(error) = welcome_window.eval(&script) {
        log::error!("failed to navigate welcome window to launch error page: {error}");
    }
}
