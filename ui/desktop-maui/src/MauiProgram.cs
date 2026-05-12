using Microsoft.Extensions.Logging;

namespace UzoncalcMaui;

public static class MauiProgram
{
    public static MauiApp CreateMauiApp()
    {
        var builder = MauiApp.CreateBuilder();
        builder
            .UseMauiApp<App>()
            .ConfigureFonts(fonts =>
            {
                fonts.AddFont("OpenSans-Regular.ttf", "OpenSansRegular");
                fonts.AddFont("OpenSans-Semibold.ttf", "OpenSansSemibold");
            });

#if DEBUG
        builder.Logging.AddDebug();
        builder.Services.AddLogging(configure => configure.AddDebug());
#endif

        builder.Services.AddSingleton(new AppHostOptions());
        builder.Services.AddSingleton<ILocalServiceBootstrapper, LocalServiceBootstrapper>();
        builder.Services.AddTransient<WebShellPage>();

        return builder.Build();
    }
}
