mod response;
mod routes;
mod state;

use axum::{http::Method, Router};
use std::error::Error;
use tokio::net::TcpListener;
use tower_http::cors::{Any, CorsLayer};

pub use state::SharedState;

pub const LANGUAGE_SERVICE_ADDR: &str = "127.0.0.1:38472";

pub fn spawn_language_server(state: SharedState) {
    tauri::async_runtime::spawn(async move {
        if let Err(error) = run_language_server(state).await {
            log::error!("language service failed: {error}");
        }
    });
}

async fn run_language_server(state: SharedState) -> Result<(), Box<dyn Error + Send + Sync>> {
    let cors = CorsLayer::new()
        .allow_origin(Any)
        .allow_methods([Method::GET, Method::POST, Method::OPTIONS])
        .allow_headers(Any);

    let app = Router::new()
        .nest("/api", routes::router())
        .layer(cors)
        .with_state(state);

    let listener = TcpListener::bind(LANGUAGE_SERVICE_ADDR).await?;
    log::info!("language service listening on http://{LANGUAGE_SERVICE_ADDR}");
    axum::serve(listener, app).await?;
    Ok(())
}
