namespace UzoncalcMaui.ShellHost;

public sealed class AppHostOptions
{
    public string AppUrl { get; init; } = "http://localhost:3346/";

    public string HealthCheckUrl { get; init; } = "http://127.0.0.1:3346/";

    public int StartupTimeoutSeconds { get; init; } = 30;
}
