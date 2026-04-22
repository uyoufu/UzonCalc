# Desktop MAUI Windows Deploy

This directory contains a PowerShell entry script that builds the `publish/win` output tree in one command.

## Prerequisites

- Windows PowerShell or PowerShell 7
- .NET SDK with the MAUI Windows workload installed
- A local environment that can run `dotnet publish`
- Whatever is required to run `ui/api/scripts/build-portable.ps1`

## Usage

```powershell
powershell -ExecutionPolicy Bypass -File ui\desktop-maui\scripts\deploy.ps1
```

Optional parameters:

```powershell
powershell -ExecutionPolicy Bypass -File ui\desktop-maui\scripts\deploy.ps1 `
  -Configuration Release `
  -Framework net10.0-windows10.0.19041.0 `
  -RuntimeIdentifier win-x64 `
  -PythonVersion 3.11.9 `
  -SkipApiBuild `
  -SkipMauiPublish
```

Defaults are defined in `deploy_config.ps1`:

- `Configuration = Release`
- `Framework = net10.0-windows10.0.19041.0`
- `RuntimeIdentifier = ""` (empty by default, only pass `-RuntimeIdentifier` when you need RID-specific output)
- `PythonVersion = 3.11.9`
- `PublishRoot = <repo>\publish\win`

## Output Layout

The script deletes and recreates `publish/win`, then produces:

```text
publish/
  win/
    core/
      api/
      python/
      uzoncalc/
    maui/
```

- `core/api` is rebuilt from `ui/api/scripts/build-portable.ps1`
- `core/python` is copied from `dist/python-embedded`
- `core/uzoncalc` is copied from the repository root `uzoncalc`
- `maui` is produced by `dotnet publish ui/desktop-maui/uzoncalc/uzoncalc.csproj`

The script does not create a zip archive. The directory tree itself is the release artifact.
