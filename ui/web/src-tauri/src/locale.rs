pub const DEFAULT_LOCALE: &str = "zh-CN";
pub const EN_US_LOCALE: &str = "en-US";
pub const SUPPORTED_LOCALES: [&str; 2] = [DEFAULT_LOCALE, EN_US_LOCALE];

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

pub fn duplicate_instance_message() -> String {
    t!("app.duplicate_instance_message").to_string()
}

pub fn tray_quit_text() -> String {
    t!("tray.quit").to_string()
}

pub fn unsupported_language_message() -> String {
    t!("language.unsupported").to_string()
}
