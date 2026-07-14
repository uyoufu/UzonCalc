use tauri::{LogicalSize, Size, WebviewWindow};

const LAUNCH_ERROR_WINDOW_WIDTH: f64 = 800.0;
const LAUNCH_ERROR_WINDOW_HEIGHT: f64 = 540.0;

pub fn show_launch_error(welcome_window: WebviewWindow, error_message: String) {
    log::warn!("showing launch error page: {error_message}");

    resize_for_launch_error(&welcome_window);

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

fn resize_for_launch_error(welcome_window: &WebviewWindow) {
    let size = Size::Logical(LogicalSize {
        width: LAUNCH_ERROR_WINDOW_WIDTH,
        height: LAUNCH_ERROR_WINDOW_HEIGHT,
    });

    if let Err(error) = welcome_window.set_size(size) {
        log::warn!("failed to resize launch error window: {error}");
    }

    if let Err(error) = welcome_window.center() {
        log::debug!("failed to center launch error window: {error}");
    }
}
