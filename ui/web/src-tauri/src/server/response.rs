use axum::{http::StatusCode, Json};
use serde::Serialize;

#[derive(Debug, Serialize)]
pub struct ApiResponse<T>
where
    T: Serialize,
{
    data: Option<T>,
    code: u16,
    message: String,
    ok: bool,
}

impl<T> ApiResponse<T>
where
    T: Serialize,
{
    pub fn ok(data: T) -> Self {
        Self {
            data: Some(data),
            code: StatusCode::OK.as_u16(),
            message: "ok".to_string(),
            ok: true,
        }
    }
}

impl ApiResponse<()> {
    pub fn error(status_code: StatusCode, message: String) -> Self {
        Self {
            data: None,
            code: status_code.as_u16(),
            message,
            ok: false,
        }
    }
}

pub type ApiJson<T> = Json<ApiResponse<T>>;
pub type ApiError = (StatusCode, Json<ApiResponse<()>>);

pub fn ok<T>(data: T) -> ApiJson<T>
where
    T: Serialize,
{
    Json(ApiResponse::ok(data))
}

pub fn error(status_code: StatusCode, message: String) -> ApiError {
    (status_code, Json(ApiResponse::error(status_code, message)))
}
