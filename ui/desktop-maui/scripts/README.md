# Desktop MAUI Windows Deploy

The desktop deploy entry script lives in the repository root `scripts/` directory and builds the `publish/win` output tree in one command.

## Prerequisites

- Windows PowerShell or PowerShell 7
- .NET SDK with the MAUI Windows workload installed
- A local environment that can run `dotnet publish`
- Whatever is required to run `ui/api/scripts/build-portable.ps1`

## Usage

```powershell
powershell -ExecutionPolicy Bypass -File scripts\deploy.ps1
```

Optional parameters:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\deploy.ps1 `
  -Configuration Release `
  -Framework net10.0-windows10.0.19041.0 `
  -RuntimeIdentifier win-x64 `
  -PythonVersion 3.11.9 `
  -PythonCacheRoot .cache\desktop-maui\python `
  -SkipApiBuild `
  -SkipMauiPublish
```

Defaults are defined in `scripts/deploy_config.ps1`:

- `Configuration = Release`
- `Framework = net10.0-windows10.0.19041.0`
- `RuntimeIdentifier = win-x64`
- `SatelliteResourceLanguages = zh-Hans;zh-Hant;en`
- `PythonVersion = 3.11.9`
- `PythonCacheRoot = <repo>\.cache\desktop-maui\python`
- `PublishRoot = <repo>\publish\win`

## Output Layout

The script deletes and recreates `publish/win`, then produces:

```text
publish/
  win/
    UzoncalcMaui.exe
    ...
    core/
      api/
      python/
      uzoncalc/
```

- `core/api` is rebuilt from `ui/api/scripts/build-portable.ps1`
- `core/python` is copied from `dist/python-embedded`
- `core/uzoncalc` is copied from the repository root `uzoncalc`
- The MAUI app is published directly into `publish/win` as a self-contained single-file Windows app
- Satellite resource languages are limited by `SatelliteResourceLanguages` in `scripts/deploy_config.ps1`
- Embedded Python is cached under `.cache/desktop-maui/python` and reused while the Python version, architecture, and API `requirements.txt` hash are unchanged

The script does not create a zip archive. The directory tree itself is the release artifact.
