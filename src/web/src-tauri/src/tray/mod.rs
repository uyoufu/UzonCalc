use std::error::Error;
use tauri::{
    menu::{Menu, MenuItem},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
    AppHandle, Manager, WebviewWindow, WindowEvent,
};

use crate::{
    api_process::ApiProcessState,
    locale::{app_title, tray_quit_text, tray_show_text},
};

const TRAY_ID: &str = "main-tray";
const SHOW_MENU_ID: &str = "show";
const QUIT_MENU_ID: &str = "quit";

#[derive(Clone)]
pub struct TrayState {
    tray_id: String,
    show_item: MenuItem<tauri::Wry>,
    quit_item: MenuItem<tauri::Wry>,
}

impl TrayState {
    pub fn apply_locale(&self, app: &AppHandle) {
        if let Err(error) = self.show_item.set_text(tray_show_text()) {
            log::error!("failed to update tray show text: {error}");
        }

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

pub fn setup_tray(
    app: &tauri::App,
    main_window: &WebviewWindow,
    startup_window: &WebviewWindow,
) -> Result<TrayState, Box<dyn Error>> {
    let show = MenuItem::with_id(app, SHOW_MENU_ID, tray_show_text(), true, None::<&str>)?;
    let quit = MenuItem::with_id(app, QUIT_MENU_ID, tray_quit_text(), true, None::<&str>)?;
    let menu = Menu::with_items(app, &[&show, &quit])?;
    let main_window_label = main_window.label().to_string();
    let startup_window_label = startup_window.label().to_string();
    let menu_main_window_label = main_window_label.clone();
    let menu_startup_window_label = startup_window_label.clone();
    let title = app_title();
    let mut tray_builder = TrayIconBuilder::with_id(TRAY_ID)
        .menu(&menu)
        .tooltip(&title)
        .title(&title)
        .show_menu_on_left_click(false)
        .on_menu_event(move |app, event| match event.id().as_ref() {
            SHOW_MENU_ID => {
                show_active_window(app, &menu_main_window_label, &menu_startup_window_label);
            }
            QUIT_MENU_ID => {
                stop_api_process(app);
                app.exit(0);
            }
            _ => {}
        })
        .on_tray_icon_event(move |tray, event| {
            if let TrayIconEvent::Click {
                button: MouseButton::Left,
                button_state: MouseButtonState::Up,
                ..
            } = event
            {
                toggle_active_window(
                    tray.app_handle(),
                    &main_window_label,
                    &startup_window_label,
                );
            }
        });

    if let Some(icon) = app.default_window_icon().cloned() {
        tray_builder = tray_builder.icon(icon);
    }

    tray_builder.build(app)?;

    let main_window_to_hide = main_window.clone();
    main_window.on_window_event(move |event| {
        if let WindowEvent::CloseRequested { api, .. } = event {
            api.prevent_close();
            if let Err(error) = main_window_to_hide.hide() {
                log::error!("failed to hide window to tray: {error}");
            }
        }
    });

    Ok(TrayState {
        tray_id: TRAY_ID.to_string(),
        show_item: show,
        quit_item: quit,
    })
}

fn stop_api_process(app: &AppHandle) {
    let Some(api_process) = app.try_state::<ApiProcessState>() else {
        log::warn!("api process state is not available while quitting from tray");
        return;
    };

    api_process.stop();
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

fn toggle_active_window(
    app: &AppHandle,
    main_window_label: &str,
    startup_window_label: &str,
) {
    if let Some(window) = app.get_webview_window(startup_window_label) {
        toggle_window_visibility(&window);
        return;
    }

    if let Some(window) = app.get_webview_window(main_window_label) {
        toggle_window_visibility(&window);
        return;
    }

    log::warn!("no window found while toggling from tray");
}

fn show_active_window(app: &AppHandle, main_window_label: &str, startup_window_label: &str) {
    if let Some(window) = app
        .get_webview_window(startup_window_label)
        .or_else(|| app.get_webview_window(main_window_label))
    {
        show_and_focus_window(&window);
        return;
    }

    log::warn!("no window found while showing from tray menu");
}

fn show_and_focus_window(window: &WebviewWindow) {
    if let Err(error) = window.show() {
        log::error!("failed to show window from tray menu: {error}");
        return;
    }

    if let Err(error) = window.unminimize() {
        log::debug!("failed to unminimize window from tray menu: {error}");
    }

    if let Err(error) = window.set_focus() {
        log::error!("failed to focus window from tray menu: {error}");
    }
}
