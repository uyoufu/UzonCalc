namespace uzoncalc.ShellHost;

public sealed record ServiceBootstrapResult(
    bool Success,
    bool ShouldNavigate,
    string StatusMessage,
    string? ErrorMessage = null)
{
    public static ServiceBootstrapResult Started(string message) =>
        new(true, true, message);

    public static ServiceBootstrapResult Reused(string message) =>
        new(true, true, message);

    public static ServiceBootstrapResult Skipped(string message) =>
        new(true, true, message);

    public static ServiceBootstrapResult Failed(string message) =>
        new(false, false, "Startup failed.", message);
}
