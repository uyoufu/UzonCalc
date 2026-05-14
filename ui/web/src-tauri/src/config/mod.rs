use serde::Deserialize;
use std::{
    error::Error,
    fs,
    path::{Path, PathBuf},
};
use tauri::{Manager, WebviewUrl};

const CONFIG_FILE_NAME: &str = "config.toml";

#[derive(Debug, Clone, Default, Deserialize)]
pub struct AppConfig {
    pub webview: Option<WebviewConfig>,
}

#[derive(Debug, Clone, Deserialize)]
pub struct WebviewConfig {
    pub url: Option<String>,
}

impl AppConfig {
    pub fn webview_url(&self) -> Option<WebviewUrl> {
        let url = self.webview.as_ref()?.url.as_ref()?.trim();

        if url.is_empty() {
            return None;
        }

        Some(parse_webview_url(url))
    }
}

pub fn load_app_config(app: &tauri::App) -> AppConfig {
    config_paths(app)
        .into_iter()
        .find_map(|path| match read_app_config(&path) {
            Ok(Some(config)) => {
                log::info!("using config from {}", path.display());
                Some(config)
            }
            Ok(None) => None,
            Err(error) => {
                log::warn!("failed to load {}: {error}", path.display());
                None
            }
        })
        .unwrap_or_default()
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

fn read_app_config(path: &Path) -> Result<Option<AppConfig>, Box<dyn Error>> {
    if !path.exists() {
        return Ok(None);
    }

    let config = toml::from_str(&fs::read_to_string(path)?)?;
    Ok(Some(config))
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
