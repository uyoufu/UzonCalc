use std::error::Error;
use tauri::{
    menu::{Menu, MenuItem},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
    AppHandle, Manager, WebviewWindow, WindowEvent,
};

use crate::locale::{app_title, tray_quit_text};

const TRAY_ID: &str = "main-tray";
const QUIT_MENU_ID: &str = "quit";

#[derive(Clone)]
pub struct TrayState {
    tray_id: String,
    quit_item: MenuItem<tauri::Wry>,
}

impl TrayState {
    pub fn apply_locale(&self, app: &AppHandle) {
        if let Err(error) = self.quit_item.set_text(tray_quit_text()) {
            log::error!("failed to update tray quit text: {error}");
        }

        let title = app_title();
        let Some(tray) = app.tray_by_id(&self.tray_id) else {
            log::warn!("tray {} not found while applying locale", self.tray_id);
            return;
        };

        if let Err(error) = tray.set_tooltip(Some(&title)) {
            log::debug!("failed to update tray tooltip: {error}");
        }

        if let Err(error) = tray.set_title(Some(&title)) {
            log::debug!("failed to update tray title: {error}");
        }
    }
}

pub fn setup_tray(app: &tauri::App, window: &WebviewWindow) -> Result<TrayState, Box<dyn Error>> {
    let quit = MenuItem::with_id(app, QUIT_MENU_ID, tray_quit_text(), true, None::<&str>)?;
    let menu = Menu::with_items(app, &[&quit])?;
    let window_label = window.label().to_string();
    let title = app_title();
    let mut tray_builder = TrayIconBuilder::with_id(TRAY_ID)
        .menu(&menu)
        .tooltip(&title)
        .title(&title)
        .show_menu_on_left_click(false)
        .on_menu_event(|app, event| {
            if event.id().as_ref() == QUIT_MENU_ID {
                app.exit(0);
            }
        })
        .on_tray_icon_event(move |tray, event| {
            if let TrayIconEvent::Click {
                button: MouseButton::Left,
                button_state: MouseButtonState::Up,
                ..
            } = event
            {
                if let Some(window) = tray.app_handle().get_webview_window(&window_label) {
                    toggle_window_visibility(&window);
                }
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

    Ok(TrayState {
        tray_id: TRAY_ID.to_string(),
        quit_item: quit,
    })
}

fn toggle_window_visibility(window: &WebviewWindow) {
    match window.is_visible() {
        Ok(true) => {
            if let Err(error) = window.hide() {
                log::error!("failed to hide window from tray: {error}");
            }
        }
        Ok(false) => {
            if let Err(error) = window.show() {
                log::error!("failed to show window from tray: {error}");
                return;
            }

            if let Err(error) = window.set_focus() {
                log::error!("failed to focus window from tray: {error}");
            }
        }
        Err(error) => {
            log::error!("failed to read window visibility from tray: {error}");
        }
    }
}
