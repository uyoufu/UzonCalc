mod health_check;
mod language;

use axum::Router;

use super::SharedState;

pub fn router() -> Router<SharedState> {
    Router::new()
        .merge(health_check::router())
        .merge(language::router())
}
