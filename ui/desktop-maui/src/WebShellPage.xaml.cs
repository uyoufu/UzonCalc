namespace UzoncalcMaui;

public partial class WebShellPage : ContentPage
{
    private readonly AppHostOptions _options;
    private readonly ILocalServiceBootstrapper _serviceBootstrapper;

    private CancellationTokenSource? _lifecycleCts;
    private bool _isStarted;

    public WebShellPage(
        AppHostOptions options,
        ILocalServiceBootstrapper serviceBootstrapper)
    {
        _options = options;
        _serviceBootstrapper = serviceBootstrapper;

        InitializeComponent();

        Loaded += OnLoaded;
        Unloaded += OnUnloaded;
    }

    private async void OnLoaded(object? sender, EventArgs e)
    {
        if (_isStarted)
        {
            return;
        }

        _isStarted = true;
        _lifecycleCts = new CancellationTokenSource();

        await InitializeAsync(_lifecycleCts.Token);
    }

    private async void OnUnloaded(object? sender, EventArgs e)
    {
        _lifecycleCts?.Cancel();

        try
        {
            await _serviceBootstrapper.StopAsync(CancellationToken.None);
        }
        catch
        {
            // Ignore shutdown exceptions during window teardown.
        }
    }

    private async void RetryButton_OnClicked(object? sender, EventArgs e)
    {
        await InitializeAsync(CancellationToken.None);
    }

    private async Task InitializeAsync(CancellationToken cancellationToken)
    {
        ShowLoading("Starting local service...");

        var result = await _serviceBootstrapper.StartAsync(cancellationToken);
        if (!result.Success || !result.ShouldNavigate)
        {
            ShowError(result.ErrorMessage ?? "Unknown startup error.");
            return;
        }

        StatusLabel.Text = result.StatusMessage;
        ErrorView.IsVisible = false;
        AppWebView.IsVisible = true;
        AppWebView.Source = _options.AppUrl;
        LoadingView.IsVisible = false;
    }

    private void ShowLoading(string message)
    {
        StatusLabel.Text = message;
        ErrorView.IsVisible = false;
        AppWebView.IsVisible = false;
        LoadingView.IsVisible = true;
    }

    private void ShowError(string message)
    {
        ErrorLabel.Text = message;
        LoadingView.IsVisible = false;
        AppWebView.IsVisible = false;
        ErrorView.IsVisible = true;
    }
}
