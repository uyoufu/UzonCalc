use axum::{routing::get, Router};

use crate::server::{response, SharedState};

pub fn router() -> Router<SharedState> {
    Router::new().route("/health-check", get(health_check))
}

async fn health_check() -> response::ApiJson<bool> {
    response::ok(true)
}
