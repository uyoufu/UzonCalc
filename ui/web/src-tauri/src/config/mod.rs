use serde::{Deserialize, Serialize};
use std::{
    error::Error,
    fs, io,
    path::{Path, PathBuf},
};
use tauri::{Manager, WebviewUrl};

use crate::locale::{AppLocale, DEFAULT_LOCALE};

const CONFIG_FILE_NAME: &str = "config.toml";

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct AppConfig {
    #[serde(default)]
    pub webview: Option<WebviewConfig>,
    #[serde(default = "default_language")]
    pub language: String,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct WebviewConfig {
    pub url: Option<String>,
}

impl Default for AppConfig {
    fn default() -> Self {
        Self {
            webview: None,
            language: default_language(),
        }
    }
}

impl AppConfig {
    pub fn webview_url(&self) -> Option<WebviewUrl> {
        let url = self.webview.as_ref()?.url.as_ref()?.trim();

        if url.is_empty() {
            return None;
        }

        Some(parse_webview_url(url))
    }

    pub fn locale(&self) -> AppLocale {
        AppLocale::parse(&self.language).unwrap_or(AppLocale::ZhCn)
    }

    pub fn set_locale(&mut self, locale: AppLocale) {
        self.language = locale.as_str().to_string();
    }
}

pub fn load_app_config(app: &tauri::App) -> AppConfig {
    app_config_paths(app)
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

pub fn app_config_paths(app: &tauri::App) -> Vec<PathBuf> {
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

pub fn save_app_config(
    paths: &[PathBuf],
    config: &AppConfig,
) -> Result<PathBuf, Box<dyn Error + Send + Sync>> {
    let config_content = toml::to_string_pretty(config)?;
    let mut last_error = None;

    for path in paths {
        match write_app_config(path, &config_content) {
            Ok(()) => {
                log::info!("saved config to {}", path.display());
                return Ok(path.clone());
            }
            Err(error) => {
                log::warn!("failed to save {}: {error}", path.display());
                last_error = Some(error);
            }
        }
    }

    Err(last_error
        .unwrap_or_else(|| io::Error::new(io::ErrorKind::NotFound, "no config path available"))
        .into())
}

fn read_app_config(path: &Path) -> Result<Option<AppConfig>, Box<dyn Error>> {
    if !path.exists() {
        return Ok(None);
    }

    let config = toml::from_str(&fs::read_to_string(path)?)?;
    Ok(Some(config))
}

fn write_app_config(path: &Path, config_content: &str) -> io::Result<()> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)?;
    }

    fs::write(path, config_content)
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

fn default_language() -> String {
    DEFAULT_LOCALE.to_string()
}
