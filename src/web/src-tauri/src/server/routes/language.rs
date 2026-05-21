use axum::{extract::State, http::StatusCode, routing::get, Json, Router};
use serde::{Deserialize, Serialize};

use crate::{
    locale::{unsupported_language_message, AppLocale, SUPPORTED_LOCALES},
    server::{response, SharedState},
};

#[derive(Debug, Deserialize)]
struct SetLanguageRequest {
    language: String,
}

#[derive(Debug, Serialize)]
struct LanguageResponse {
    language: String,
    supported_languages: Vec<&'static str>,
}

impl LanguageResponse {
    fn new(locale: AppLocale) -> Self {
        Self {
            language: locale.as_str().to_string(),
            supported_languages: SUPPORTED_LOCALES.to_vec(),
        }
    }
}

pub fn router() -> Router<SharedState> {
    Router::new().route("/language", get(get_language).post(set_language))
}

async fn get_language(State(state): State<SharedState>) -> response::ApiJson<LanguageResponse> {
    response::ok(LanguageResponse::new(state.current_locale()))
}

async fn set_language(
    State(state): State<SharedState>,
    Json(payload): Json<SetLanguageRequest>,
) -> Result<response::ApiJson<LanguageResponse>, response::ApiError> {
    let locale = AppLocale::parse(&payload.language)
        .ok_or_else(|| response::error(StatusCode::BAD_REQUEST, unsupported_language_message()))?;

    state
        .apply_locale(locale)
        .map_err(|message| response::error(StatusCode::INTERNAL_SERVER_ERROR, message))?;

    Ok(response::ok(LanguageResponse::new(locale)))
}
