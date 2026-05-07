using Microsoft.Extensions.DependencyInjection;

namespace uzoncalc;

public partial class App : Application
{
    private readonly IServiceProvider _serviceProvider;

    public App(IServiceProvider serviceProvider)
    {
        _serviceProvider = serviceProvider;
        InitializeComponent();
    }

    protected override Window CreateWindow(IActivationState? activationState)
    {
        var page = _serviceProvider.GetRequiredService<WebShellPage>();

        return new Window(page)
        {
            Title = "宇正群邮 | UzonCalc",
        };
    }
}
