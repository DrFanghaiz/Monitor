$ErrorActionPreference = 'Stop'

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $scriptRoot '..'))
$repoPrefix = $repoRoot.TrimEnd('\') + '\'

$projectPath = Join-Path $repoRoot 'src\Monitor.App\Monitor.App.csproj'
$publishDir = Join-Path $repoRoot 'artifacts\publish\Monitor'
$installerDir = Join-Path $repoRoot 'artifacts\installer'
$cloudflaredPath = Join-Path $repoRoot 'cloudflared.exe'
$issPath = Join-Path $scriptRoot 'Monitor.iss'

function Assert-WorkspacePath([string]$path) {
    $fullPath = [System.IO.Path]::GetFullPath($path)
    if (-not $fullPath.StartsWith($repoPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to touch path outside workspace: $fullPath"
    }
}

Assert-WorkspacePath $publishDir
Assert-WorkspacePath $installerDir

if (-not (Test-Path $projectPath)) {
    throw "Project file not found: $projectPath"
}

if (-not (Test-Path $cloudflaredPath)) {
    throw "cloudflared.exe not found: $cloudflaredPath"
}

if (Test-Path $publishDir) {
    Remove-Item -LiteralPath $publishDir -Recurse -Force
}

New-Item -ItemType Directory -Path $publishDir -Force | Out-Null
New-Item -ItemType Directory -Path $installerDir -Force | Out-Null

Write-Host "Publishing self-contained win-x64 build..."
& dotnet publish $projectPath `
    -c Release `
    -r win-x64 `
    --self-contained true `
    -p:PublishSingleFile=false `
    -p:SatelliteResourceLanguages=zh-Hans `
    -p:DebugType=None `
    -p:DebugSymbols=false `
    -o $publishDir

if ($LASTEXITCODE -ne 0) {
    throw "dotnet publish failed"
}

if (-not (Test-Path (Join-Path $publishDir 'cloudflared.exe'))) {
    Copy-Item -LiteralPath $cloudflaredPath -Destination (Join-Path $publishDir 'cloudflared.exe') -Force
}

$isccCandidates = @()
$isccCommand = Get-Command iscc.exe -ErrorAction SilentlyContinue
if ($isccCommand) {
    $isccCandidates += $isccCommand.Source
}
$isccCandidates += @(
    (Join-Path ${env:ProgramFiles(x86)} 'Inno Setup 6\ISCC.exe'),
    (Join-Path $env:ProgramFiles 'Inno Setup 6\ISCC.exe')
)

$isccPath = $isccCandidates | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
if (-not $isccPath) {
    throw "Inno Setup 6 not found. Publish output is ready at: $publishDir"
}

Write-Host "Compiling installer..."
& $isccPath $issPath

if ($LASTEXITCODE -ne 0) {
    throw "Inno Setup compile failed"
}

$setupPath = Join-Path $installerDir 'Monitor-Setup.exe'
if (-not (Test-Path $setupPath)) {
    throw "Installer not generated: $setupPath"
}

Write-Host "Installer created: $setupPath"
