use crate::{
    api_process::ApiProcessState,
    locale::{app_title, welcome_texts},
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
    let texts = serde_json::to_string(&welcome_texts())?;
    Ok(format!("window.__UZON_WELCOME_TEXTS__ = {texts};"))
}

pub fn start_api_and_finish_welcome(
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
