using System.Diagnostics;
using Microsoft.Extensions.Logging;

namespace UzoncalcMaui.ShellHost;

public sealed class LocalServiceBootstrapper : ILocalServiceBootstrapper
{
    private readonly AppHostOptions _options;
    private readonly ILogger<LocalServiceBootstrapper> _logger;
    private readonly HttpClient _httpClient;
    private readonly SemaphoreSlim _gate = new(1, 1);

    private Process? _ownedProcess;

    public LocalServiceBootstrapper(
        AppHostOptions options,
        ILogger<LocalServiceBootstrapper> logger
    )
    {
        _options = options;
        _logger = logger;
        _httpClient = new HttpClient { Timeout = TimeSpan.FromSeconds(2), };
    }

    public async Task<ServiceBootstrapResult> StartAsync(CancellationToken cancellationToken)
    {
        await _gate.WaitAsync(cancellationToken);

        try
        {
            if (await IsHealthyAsync(cancellationToken))
            {
                return ServiceBootstrapResult.Reused("Reusing service at http://localhost:3346/.");
            }

            if (!ShouldStartLocalService())
            {
                return ServiceBootstrapResult.Skipped(
                    "Local auto-start is skipped on this platform. Loading the configured URL."
                );
            }

            var launch = ResolveLaunchCommand();
            if (launch is null)
            {
                return ServiceBootstrapResult.Failed(
                    "Could not locate ui/api/main.py or a usable Python runtime."
                );
            }

            var startInfo = new ProcessStartInfo
            {
                FileName = launch.FileName,
                Arguments = launch.Arguments,
                WorkingDirectory = launch.WorkingDirectory,
                UseShellExecute = false,
                CreateNoWindow = true,
            };

#if WINDOWS
            startInfo.WindowStyle = ProcessWindowStyle.Hidden;
#endif

            _logger.LogInformation(
                "Starting local API service with command: {FileName} {Arguments}",
                startInfo.FileName,
                startInfo.Arguments
            );

            _ownedProcess = Process.Start(startInfo);
            if (_ownedProcess is null)
            {
                return ServiceBootstrapResult.Failed("The local API process could not be started.");
            }

            var isReady = await WaitForHealthyAsync(
                TimeSpan.FromSeconds(_options.StartupTimeoutSeconds),
                cancellationToken
            );
            if (!isReady)
            {
                await StopOwnedProcessAsync();
                return ServiceBootstrapResult.Failed(
                    "The local API service did not become healthy before the startup timeout expired."
                );
            }

            return ServiceBootstrapResult.Started(
                "Local API started. Loading http://localhost:3346/."
            );
        }
        catch (OperationCanceledException)
        {
            throw;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Local service bootstrap failed.");
            await StopOwnedProcessAsync();
            return ServiceBootstrapResult.Failed(ex.Message);
        }
        finally
        {
            _gate.Release();
        }
    }

    public async Task StopAsync(CancellationToken cancellationToken)
    {
        await _gate.WaitAsync(cancellationToken);

        try
        {
            await StopOwnedProcessAsync();
        }
        finally
        {
            _gate.Release();
        }
    }

    private bool ShouldStartLocalService()
    {
        return OperatingSystem.IsWindows();
    }

    private async Task<bool> WaitForHealthyAsync(
        TimeSpan timeout,
        CancellationToken cancellationToken
    )
    {
        using var timeoutCts = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
        timeoutCts.CancelAfter(timeout);

        while (!timeoutCts.Token.IsCancellationRequested)
        {
            if (await IsHealthyAsync(timeoutCts.Token))
            {
                return true;
            }

            if (_ownedProcess is not null && _ownedProcess.HasExited)
            {
                _logger.LogWarning(
                    "Local API process exited early with code {ExitCode}.",
                    _ownedProcess.ExitCode
                );
                return false;
            }

            await Task.Delay(TimeSpan.FromMilliseconds(500), timeoutCts.Token);
        }

        return false;
    }

    private async Task<bool> IsHealthyAsync(CancellationToken cancellationToken)
    {
        try
        {
            using var response = await _httpClient.GetAsync(
                _options.HealthCheckUrl,
                cancellationToken
            );
            return response.IsSuccessStatusCode;
        }
        catch (Exception ex)
            when (ex is HttpRequestException or TaskCanceledException or InvalidOperationException)
        {
            return false;
        }
    }

    private async Task StopOwnedProcessAsync()
    {
        if (_ownedProcess is null)
        {
            return;
        }

        try
        {
            if (!_ownedProcess.HasExited)
            {
                _logger.LogInformation(
                    "Stopping owned local API process {ProcessId}.",
                    _ownedProcess.Id
                );
                _ownedProcess.Kill(entireProcessTree: true);
                await _ownedProcess.WaitForExitAsync();
            }
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Failed to stop the owned local API process cleanly.");
        }
        finally
        {
            _ownedProcess.Dispose();
            _ownedProcess = null;
        }
    }

    private LaunchCommand? ResolveLaunchCommand()
    {
        var projectRoot = FindProjectRoot();
        if (projectRoot is null)
        {
            return null;
        }

        var apiDir = Path.Combine(projectRoot, "ui", "api");
        var apiEntry = Path.Combine(apiDir, "main.py");
        if (!File.Exists(apiEntry))
        {
            return null;
        }

        var configuredPython = Environment.GetEnvironmentVariable("UZONCALC_PYTHON");
        if (!string.IsNullOrWhiteSpace(configuredPython))
        {
            return new LaunchCommand(configuredPython, $"\"{apiEntry}\"", apiDir);
        }

        var bundledPython = Path.Combine(projectRoot, ".venv", "Scripts", "python.exe");
        if (File.Exists(bundledPython))
        {
            return new LaunchCommand(bundledPython, $"\"{apiEntry}\"", apiDir);
        }

        if (OperatingSystem.IsWindows())
        {
            return new LaunchCommand("py", $"-3 \"{apiEntry}\"", apiDir);
        }

        return new LaunchCommand("python3", $"\"{apiEntry}\"", apiDir);
    }

    private static string? FindProjectRoot()
    {
        foreach (var seed in EnumerateProbeDirectories())
        {
            var current = new DirectoryInfo(seed);
            while (current is not null)
            {
                var candidate = Path.Combine(current.FullName, "ui", "api", "main.py");
                if (File.Exists(candidate))
                {
                    return current.FullName;
                }

                current = current.Parent;
            }
        }

        return null;
    }

    private static IEnumerable<string> EnumerateProbeDirectories()
    {
        yield return AppContext.BaseDirectory;
        yield return Environment.CurrentDirectory;
    }

    private sealed record LaunchCommand(string FileName, string Arguments, string WorkingDirectory);
}
