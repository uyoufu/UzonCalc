use std::error::Error;
use tauri::{
    menu::{Menu, MenuItem},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
    Manager, WebviewWindow, WindowEvent,
};

const QUIT_MENU_ID: &str = "quit";

pub fn setup_tray(app: &mut tauri::App, window: &WebviewWindow) -> Result<(), Box<dyn Error>> {
    let quit = MenuItem::with_id(app, QUIT_MENU_ID, "退出", true, None::<&str>)?;
    let menu = Menu::with_items(app, &[&quit])?;
    let window_label = window.label().to_string();
    let mut tray_builder = TrayIconBuilder::new()
        .menu(&menu)
        .tooltip("UzonCalc")
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

    Ok(())
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
