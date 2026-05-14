pub mod config;
pub mod tray;

use config::{load_app_config, AppConfig};
use std::error::Error;
use tauri::{Manager, WebviewWindow, WebviewWindowBuilder};

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .setup(|app| {
            if cfg!(debug_assertions) {
                app.handle().plugin(
                    tauri_plugin_log::Builder::default()
                        .level(log::LevelFilter::Info)
                        .build(),
                )?;
            }

            let app_config = load_app_config(app);
            let window = create_main_window(app, &app_config)?;
            app.manage(app_config);
            tray::setup_tray(app, &window)?;

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
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

    let window = WebviewWindowBuilder::from_config(app.handle(), &window_config)?.build()?;
    Ok(window)
}

fn missing_main_window_error() -> std::io::Error {
    std::io::Error::new(
        std::io::ErrorKind::InvalidData,
        "missing main window configuration",
    )
}
