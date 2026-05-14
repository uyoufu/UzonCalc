use serde::Deserialize;
use std::{
    error::Error,
    fs,
    path::{Path, PathBuf},
};
use tauri::{
    menu::{Menu, MenuItem},
    tray::TrayIconBuilder,
    Manager, WebviewUrl, WebviewWindow, WebviewWindowBuilder, WindowEvent,
};

const CONFIG_FILE_NAME: &str = "config.toml";
const QUIT_MENU_ID: &str = "quit";

#[derive(Debug, Deserialize)]
struct AppConfig {
    webview: Option<WebviewConfig>,
}

#[derive(Debug, Deserialize)]
struct WebviewConfig {
    url: Option<String>,
}

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

            let window = create_main_window(app)?;

            let quit = MenuItem::with_id(app, QUIT_MENU_ID, "退出", true, None::<&str>)?;
            let menu = Menu::with_items(app, &[&quit])?;
            let mut tray_builder = TrayIconBuilder::new()
                .menu(&menu)
                .tooltip("UzonCalc")
                .show_menu_on_left_click(false)
                .on_menu_event(|app, event| {
                    if event.id().as_ref() == QUIT_MENU_ID {
                        app.exit(0);
                    }
                });

            if let Some(icon) = app.default_window_icon().cloned() {
                tray_builder = tray_builder.icon(icon);
            }

            tray_builder.build(app)?;

            let window_to_hide = window.clone();
            window.on_window_event(move |event| {
                if let WindowEvent::CloseRequested { api, .. } = event {
                    api.prevent_close();
                    if let Err(error) = window_to_hide.hide() {
                        log::error!("failed to hide window to tray: {error}");
                    }
                }
            });

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

fn create_main_window(app: &mut tauri::App) -> Result<WebviewWindow, Box<dyn Error>> {
    let mut window_config = app
        .config()
        .app
        .windows
        .first()
        .cloned()
        .ok_or_else(|| missing_main_window_error())?;

    if let Some(url) = load_webview_url(app) {
        window_config.url = url;
    }

    let window = WebviewWindowBuilder::from_config(app.handle(), &window_config)?.build()?;
    Ok(window)
}

fn load_webview_url(app: &tauri::App) -> Option<WebviewUrl> {
    config_paths(app)
        .into_iter()
        .find_map(|path| match read_webview_url(&path) {
            Ok(Some(url)) => {
                log::info!("using webview url from {}", path.display());
                Some(url)
            }
            Ok(None) => None,
            Err(error) => {
                log::warn!("failed to load {}: {error}", path.display());
                None
            }
        })
}

fn config_paths(app: &tauri::App) -> Vec<PathBuf> {
    let mut paths = Vec::new();

    if let Ok(exe_path) = std::env::current_exe() {
        if let Some(exe_dir) = exe_path.parent() {
            paths.push(exe_dir.join(CONFIG_FILE_NAME));
        }
    }

    if let Ok(resource_dir) = app.path().resource_dir() {
        paths.push(resource_dir.join(CONFIG_FILE_NAME));
    }

    paths
}

fn read_webview_url(path: &Path) -> Result<Option<WebviewUrl>, Box<dyn Error>> {
    if !path.exists() {
        return Ok(None);
    }

    let config: AppConfig = toml::from_str(&fs::read_to_string(path)?)?;
    let Some(url) = config.webview.and_then(|webview| webview.url) else {
        return Ok(None);
    };

    let url = url.trim();
    if url.is_empty() {
        return Ok(None);
    }

    Ok(Some(parse_webview_url(url)))
}

fn parse_webview_url(url: &str) -> WebviewUrl {
    match tauri::Url::parse(url) {
        Ok(parsed_url) if parsed_url.scheme() == "http" || parsed_url.scheme() == "https" => {
            WebviewUrl::External(parsed_url)
        }
        Ok(parsed_url) => WebviewUrl::CustomProtocol(parsed_url),
        Err(_) => WebviewUrl::App(PathBuf::from(url)),
    }
}

fn missing_main_window_error() -> std::io::Error {
    std::io::Error::new(
        std::io::ErrorKind::InvalidData,
        "missing main window configuration",
    )
}
