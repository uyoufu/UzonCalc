use crate::server::SharedState;
use std::{
    sync::{
        atomic::{AtomicU64, Ordering},
        Arc,
    },
    thread,
    time::Duration,
};
use tauri::{WebviewWindow, WindowEvent};

const WINDOW_SIZE_SAVE_DELAY: Duration = Duration::from_millis(500);

pub(crate) fn setup_window_size_persistence(
    main_window: &WebviewWindow,
    shared_state: SharedState,
) {
    let resize_revision = Arc::new(AtomicU64::new(0));
    let resize_revision_for_handler = resize_revision.clone();

    main_window.on_window_event(move |event| {
        let WindowEvent::Resized(size) = event else {
            return;
        };

        if size.width == 0 || size.height == 0 {
            return;
        }

        let revision = resize_revision_for_handler.fetch_add(1, Ordering::SeqCst) + 1;
        let resize_revision_for_save = resize_revision_for_handler.clone();
        let shared_state = shared_state.clone();
        let width = size.width;
        let height = size.height;

        thread::spawn(move || {
            thread::sleep(WINDOW_SIZE_SAVE_DELAY);

            if resize_revision_for_save.load(Ordering::SeqCst) != revision {
                return;
            }

            if let Err(error) = shared_state.save_window_size(width, height) {
                log::warn!("failed to save window size: {error}");
            }
        });
    });
}
