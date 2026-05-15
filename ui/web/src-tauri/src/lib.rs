#[macro_use]
extern crate rust_i18n;

pub mod config;
pub mod locale;
pub mod server;
pub mod tray;

use config::{app_config_paths, load_app_config, AppConfig};
use locale::{app_title, duplicate_instance_message, set_current_locale};
use server::{spawn_language_server, SharedState};
use std::error::Error;
use tauri::{AppHandle, Manager, WebviewWindow, WebviewWindowBuilder};
use tauri_plugin_dialog::{DialogExt, MessageDialogKind};

rust_i18n::i18n!("locales");

const MAIN_WINDOW_LABEL: &str = "main";

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    set_current_locale(locale::AppLocale::ZhCn);

    let mut builder = tauri::Builder::default();

    #[cfg(desktop)]
    {
        builder = builder.plugin(tauri_plugin_single_instance::init(|app, _args, _cwd| {
            notify_duplicate_instance(app);
        }));
    }

    builder
        .plugin(tauri_plugin_dialog::init())
        .setup(|app| {
            if cfg!(debug_assertions) {
                app.handle().plugin(
                    tauri_plugin_log::Builder::default()
                        .level(log::LevelFilter::Info)
                        .build(),
                )?;
            }

            let app_config = load_app_config(app);
            set_current_locale(app_config.locale());
            let window = create_main_window(app, &app_config)?;
            let tray_state = tray::setup_tray(app, &window)?;
            let shared_state = SharedState::new(
                app.handle().clone(),
                app_config_paths(app),
                app_config,
                window.label().to_string(),
                tray_state,
            );
            app.manage(shared_state.clone());
            spawn_language_server(shared_state);

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

fn notify_duplicate_instance(app: &AppHandle) {
    if let Some(window) = app
        .get_webview_window(MAIN_WINDOW_LABEL)
        .or_else(|| app.webview_windows().into_values().next())
    {
        if let Err(error) = window.show() {
            log::error!("failed to show existing window: {error}");
        }

        if let Err(error) = window.set_focus() {
            log::error!("failed to focus existing window: {error}");
        }
    }

    app.dialog()
        .message(duplicate_instance_message())
        .kind(MessageDialogKind::Info)
        .title(app_title())
        .show(|_| {});
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

    let window = WebviewWindowBuilder::from_config(app.handle(), &window_config)?.build()?;
    Ok(window)
}

fn missing_main_window_error() -> std::io::Error {
    std::io::Error::new(
        std::io::ErrorKind::InvalidData,
        "missing main window configuration",
    )
}
