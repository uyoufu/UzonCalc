pub const DEFAULT_LOCALE: &str = "zh-CN";
pub const EN_US_LOCALE: &str = "en-US";
pub const SUPPORTED_LOCALES: [&str; 2] = [DEFAULT_LOCALE, EN_US_LOCALE];

#[derive(Debug, Clone, serde::Serialize)]
pub struct WelcomeTexts {
    pub locale: String,
    pub title: String,
    pub subtitle: String,
    pub loading: String,
    pub footer: String,
    pub html_lang: String,
}

#[derive(Debug, Clone, serde::Serialize)]
pub struct LaunchErrorTexts {
    pub locale: String,
    pub page_title: String,
    pub title: String,
    pub lead: String,
    pub details_label: String,
    pub default_error_message: String,
    pub action_restart: String,
    pub action_logs: String,
    pub html_lang: String,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum AppLocale {
    ZhCn,
    EnUs,
}

impl AppLocale {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::ZhCn => DEFAULT_LOCALE,
            Self::EnUs => EN_US_LOCALE,
        }
    }

    pub fn parse(value: &str) -> Option<Self> {
        let normalized = value.trim().replace('_', "-").to_ascii_lowercase();

        match normalized.as_str() {
            "zh" | "zh-cn" => Some(Self::ZhCn),
            "en" | "en-us" => Some(Self::EnUs),
            _ => None,
        }
    }
}

pub fn current_locale() -> AppLocale {
    AppLocale::parse(rust_i18n::locale().as_ref()).unwrap_or(AppLocale::ZhCn)
}

pub fn set_current_locale(locale: AppLocale) {
    rust_i18n::set_locale(locale.as_str());
}

pub fn app_title() -> String {
    t!("app.title").to_string()
}

pub fn tray_quit_text() -> String {
    t!("tray.quit").to_string()
}

pub fn tray_show_text() -> String {
    t!("tray.show").to_string()
}

pub fn startup_loading_text() -> String {
    t!("startup.loading").to_string()
}

pub fn welcome_texts() -> WelcomeTexts {
    WelcomeTexts {
        locale: current_locale().as_str().to_string(),
        title: t!("welcome.title").to_string(),
        subtitle: t!("welcome.subtitle").to_string(),
        loading: t!("welcome.loading").to_string(),
        footer: t!("welcome.footer").to_string(),
        html_lang: t!("welcome.html_lang").to_string(),
    }
}

pub fn launch_error_texts() -> LaunchErrorTexts {
    LaunchErrorTexts {
        locale: current_locale().as_str().to_string(),
        page_title: t!("launch_error.page_title").to_string(),
        title: t!("launch_error.title").to_string(),
        lead: t!("launch_error.lead").to_string(),
        details_label: t!("launch_error.details_label").to_string(),
        default_error_message: t!("launch_error.default_error_message").to_string(),
        action_restart: t!("launch_error.action_restart").to_string(),
        action_logs: t!("launch_error.action_logs").to_string(),
        html_lang: t!("launch_error.html_lang").to_string(),
    }
}

pub fn unsupported_language_message() -> String {
    t!("language.unsupported").to_string()
}
