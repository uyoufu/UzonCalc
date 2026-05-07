namespace uzoncalc.ShellHost;

public interface ILocalServiceBootstrapper
{
    Task<ServiceBootstrapResult> StartAsync(CancellationToken cancellationToken);

    Task StopAsync(CancellationToken cancellationToken);
}
