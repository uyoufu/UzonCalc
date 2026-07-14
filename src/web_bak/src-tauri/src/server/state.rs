use std::{
    path::PathBuf,
    sync::{Arc, Mutex},
};
use tauri::{AppHandle, Manager};

use crate::{
    config::{save_app_config, AppConfig},
    locale::{app_title, current_locale, set_current_locale, AppLocale},
    tray::TrayState,
};

#[derive(Clone)]
pub struct SharedState {
    app: AppHandle,
    config_paths: Vec<PathBuf>,
    config: Arc<Mutex<AppConfig>>,
    main_window_label: String,
    tray: TrayState,
}

impl SharedState {
    pub fn new(
        app: AppHandle,
        config_paths: Vec<PathBuf>,
        config: AppConfig,
        main_window_label: String,
        tray: TrayState,
    ) -> Self {
        Self {
            app,
            config_paths,
            config: Arc::new(Mutex::new(config)),
            main_window_label,
            tray,
        }
    }

    pub(crate) fn current_locale(&self) -> AppLocale {
        self.config
            .lock()
            .map(|config| config.locale())
            .unwrap_or_else(|_| current_locale())
    }

    pub(crate) fn apply_locale(&self, locale: AppLocale) -> Result<(), String> {
        let mut next_config = self
            .config
            .lock()
            .map_err(|_| "failed to lock app config".to_string())?
            .clone();
        next_config.set_locale(locale);

        save_app_config(&self.config_paths, &next_config).map_err(|error| error.to_string())?;

        {
            let mut config = self
                .config
                .lock()
                .map_err(|_| "failed to lock app config".to_string())?;
            *config = next_config;
        }

        set_current_locale(locale);
        self.apply_locale_to_desktop_ui();
        Ok(())
    }

    pub(crate) fn save_window_size(&self, width: u32, height: u32) -> Result<(), String> {
        let mut next_config = self
            .config
            .lock()
            .map_err(|_| "failed to lock app config".to_string())?
            .clone();
        next_config.set_window_size(width, height);

        save_app_config(&self.config_paths, &next_config).map_err(|error| error.to_string())?;

        {
            let mut config = self
                .config
                .lock()
                .map_err(|_| "failed to lock app config".to_string())?;
            *config = next_config;
        }

        Ok(())
    }

    fn apply_locale_to_desktop_ui(&self) {
        let title = app_title();

        if let Some(window) = self.app.get_webview_window(&self.main_window_label) {
            if let Err(error) = window.set_title(&title) {
                log::error!("failed to update main window title: {error}");
            }
        } else {
            log::warn!(
                "main window {} not found while applying locale",
                self.main_window_label
            );
        }

        self.tray.apply_locale(&self.app);
    }
}
