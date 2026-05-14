#requires -Version 5.1
<#
Captures local signals that may distinguish "remote tool installed/running"
from "this machine is actively being remote-controlled".

Example:
  powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\Capture-RemoteSignals.ps1 -Label todesk_idle
  powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\Capture-RemoteSignals.ps1 -Label todesk_connected -IncludeLogContent
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[A-Za-z0-9_.-]+$')]
    [string]$Label,

    [string]$OutputRoot = (Join-Path (Get-Location) 'diagnostics\remote-signals'),

    [ValidateRange(1, 1440)]
    [int]$RecentMinutes = 30,

    [switch]$IncludeLogContent,

    [switch]$SkipEventLogs,

    [switch]$SkipLogCandidates
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$script:CaptureErrors = New-Object System.Collections.Generic.List[object]
$chineseSunlogin = ([string][char]0x5411) + ([string][char]0x65E5) + ([string][char]0x8475)
$chineseRemoteDesktop = ([string][char]0x8FDC) + ([string][char]0x7A0B) + ([string][char]0x684C) + ([string][char]0x9762)

$script:RemoteKeywords = @(
    'sunlogin',
    $chineseSunlogin,
    'oray',
    'todesk',
    'anydesk',
    'teamviewer',
    'mstsc',
    'msrdc',
    'remote desktop',
    $chineseRemoteDesktop,
    'rustdesk'
)

$script:RemoteProcessNames = @(
    'sunloginclient',
    'sunloginremote',
    'sunloginservice',
    'sunloginserver',
    'orayservice',
    'todesk',
    'todesk_service',
    'todesk_lite',
    'anydesk',
    'anydesk64',
    'teamviewer',
    'teamviewer_service',
    'mstsc',
    'msrdc',
    'rustdesk',
    'rustdesk-host'
)

function Add-CaptureError {
    param(
        [Parameter(Mandatory = $true)][string]$Section,
        [Parameter(Mandatory = $true)]$ErrorRecord
    )

    $script:CaptureErrors.Add([pscustomobject]@{
        section = $Section
        message = $ErrorRecord.Exception.Message
        detail = $ErrorRecord.ToString()
    })
}

function Invoke-CaptureSection {
    param(
        [Parameter(Mandatory = $true)][string]$Section,
        [Parameter(Mandatory = $true)][scriptblock]$ScriptBlock
    )

    try {
        & $ScriptBlock
    }
    catch {
        Add-CaptureError -Section $Section -ErrorRecord $_
        @()
    }
}

function Save-Json {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        $Data
    )

    if ($null -eq $Data) {
        $Data = @()
    }

    $json = $Data | ConvertTo-Json -Depth 12
    Set-Content -LiteralPath $Path -Value $json -Encoding UTF8
}

function Test-RemoteText {
    param([string]$Value)

    if ([string]::IsNullOrWhiteSpace($Value)) {
        return $false
    }

    $lower = $Value.ToLowerInvariant()
    foreach ($keyword in $script:RemoteKeywords) {
        if ($lower.Contains($keyword.ToLowerInvariant())) {
            return $true
        }
    }
    return $false
}

function Test-RemoteProcessName {
    param([string]$Name)

    if ([string]::IsNullOrWhiteSpace($Name)) {
        return $false
    }

    $normalized = [System.IO.Path]::GetFileNameWithoutExtension($Name).ToLowerInvariant()
    return $script:RemoteProcessNames -contains $normalized
}

function Get-IsAdmin {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Get-ProcessSnapshot {
    $items = New-Object System.Collections.Generic.List[object]

    foreach ($process in Get-Process | Sort-Object ProcessName, Id) {
        $path = $null
        $startTime = $null
        try { $path = $process.Path } catch { }
        try { $startTime = $process.StartTime.ToString('yyyy-MM-dd HH:mm:ss') } catch { }

        $items.Add([pscustomobject]@{
            id = $process.Id
            name = $process.ProcessName
            path = $path
            main_window_title = $process.MainWindowTitle
            responding = $process.Responding
            start_time = $startTime
            working_set_mb = [math]::Round($process.WorkingSet64 / 1MB, 2)
            is_remote_candidate = (Test-RemoteProcessName -Name $process.ProcessName) -or
                (Test-RemoteText -Value $process.ProcessName) -or
                (Test-RemoteText -Value $process.MainWindowTitle) -or
                (Test-RemoteText -Value $path)
        })
    }

    return $items
}

function Add-WindowInteropType {
    if ('RemoteSignalWindowApi' -as [type]) {
        return
    }

    $typeDefinition = @'
using System;
using System.Runtime.InteropServices;
using System.Text;

public static class RemoteSignalWindowApi
{
    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

    [DllImport("user32.dll")]
    public static extern bool EnumWindows(EnumWindowsProc enumProc, IntPtr lParam);

    [DllImport("user32.dll")]
    public static extern bool IsWindowVisible(IntPtr hWnd);

    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    public static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);

    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    public static extern int GetWindowTextLength(IntPtr hWnd);

    [DllImport("user32.dll")]
    public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);
}
'@

    Add-Type -TypeDefinition $typeDefinition
}

function Get-WindowSnapshot {
    Add-WindowInteropType

    $processById = @{}
    foreach ($process in Get-Process) {
        $processById[$process.Id] = $process
    }

    $windows = New-Object System.Collections.Generic.List[object]
    $callback = [RemoteSignalWindowApi+EnumWindowsProc]{
        param([IntPtr]$Handle, [IntPtr]$Param)

        if (-not [RemoteSignalWindowApi]::IsWindowVisible($Handle)) {
            return $true
        }

        $length = [RemoteSignalWindowApi]::GetWindowTextLength($Handle)
        if ($length -le 0) {
            return $true
        }

        $builder = New-Object System.Text.StringBuilder ($length + 1)
        [void][RemoteSignalWindowApi]::GetWindowText($Handle, $builder, $builder.Capacity)
        $title = $builder.ToString()
        if ([string]::IsNullOrWhiteSpace($title)) {
            return $true
        }

        [uint32]$windowProcessId = 0
        [void][RemoteSignalWindowApi]::GetWindowThreadProcessId($Handle, [ref]$windowProcessId)
        $processName = $null
        $processPath = $null
        if ($processById.ContainsKey([int]$windowProcessId)) {
            $processName = $processById[[int]$windowProcessId].ProcessName
            try { $processPath = $processById[[int]$windowProcessId].Path } catch { }
        }

        $windows.Add([pscustomobject]@{
            handle = $Handle.ToInt64()
            process_id = [int]$windowProcessId
            process_name = $processName
            process_path = $processPath
            title = $title
            is_remote_candidate = (Test-RemoteText -Value $title) -or
                (Test-RemoteProcessName -Name $processName) -or
                (Test-RemoteText -Value $processPath)
        })

        return $true
    }

    [void][RemoteSignalWindowApi]::EnumWindows($callback, [IntPtr]::Zero)
    return $windows | Sort-Object process_name, title
}

function Get-ServiceSnapshot {
    Get-CimInstance Win32_Service | Sort-Object Name | ForEach-Object {
        [pscustomobject]@{
            name = $_.Name
            display_name = $_.DisplayName
            state = $_.State
            start_mode = $_.StartMode
            process_id = $_.ProcessId
            path_name = $_.PathName
            is_remote_candidate = (Test-RemoteText -Value $_.Name) -or
                (Test-RemoteText -Value $_.DisplayName) -or
                (Test-RemoteText -Value $_.PathName)
        }
    }
}

function Get-TcpConnectionSnapshot {
    $processById = @{}
    foreach ($process in Get-Process) {
        $processById[$process.Id] = $process
    }

    Get-NetTCPConnection -ErrorAction Stop |
        Where-Object { $_.State -in @('Established', 'Listen', 'SynSent', 'SynReceived') } |
        Sort-Object OwningProcess, State, RemoteAddress, RemotePort |
        ForEach-Object {
            $processName = $null
            $processPath = $null
            if ($processById.ContainsKey([int]$_.OwningProcess)) {
                $processName = $processById[[int]$_.OwningProcess].ProcessName
                try { $processPath = $processById[[int]$_.OwningProcess].Path } catch { }
            }

            [pscustomobject]@{
                local_address = $_.LocalAddress
                local_port = $_.LocalPort
                remote_address = $_.RemoteAddress
                remote_port = $_.RemotePort
                state = $_.State.ToString()
                owning_process = $_.OwningProcess
                process_name = $processName
                process_path = $processPath
                is_remote_candidate = (Test-RemoteProcessName -Name $processName) -or
                    (Test-RemoteText -Value $processName) -or
                    (Test-RemoteText -Value $processPath)
            }
        }
}

function Get-RdpEventSnapshot {
    param([datetime]$Since)

    $logs = @(
        'Microsoft-Windows-TerminalServices-LocalSessionManager/Operational',
        'Microsoft-Windows-TerminalServices-RemoteConnectionManager/Operational',
        'Microsoft-Windows-RemoteDesktopServices-RdpCoreTS/Operational',
        'Microsoft-Windows-TerminalServices-RDPClient/Operational'
    )

    $events = New-Object System.Collections.Generic.List[object]
    foreach ($logName in $logs) {
        try {
            $filter = @{
                LogName = $logName
                StartTime = $Since
            }

            Get-WinEvent -FilterHashtable $filter -ErrorAction Stop |
                Sort-Object TimeCreated |
                ForEach-Object {
                    $events.Add([pscustomobject]@{
                        log_name = $logName
                        time_created = $_.TimeCreated.ToString('yyyy-MM-dd HH:mm:ss')
                        id = $_.Id
                        provider_name = $_.ProviderName
                        level = $_.LevelDisplayName
                        message = $_.Message
                    })
                }
        }
        catch {
            Add-CaptureError -Section "event_log:$logName" -ErrorRecord $_
        }
    }

    return $events
}

function Get-RemoteToolRoots {
    $roots = New-Object System.Collections.Generic.List[string]
    $baseDirs = @(
        $env:ProgramData,
        $env:LOCALAPPDATA,
        $env:APPDATA,
        $env:ProgramFiles,
        [Environment]::GetEnvironmentVariable('ProgramFiles(x86)')
    ) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }

    $vendorDirs = @(
        'AnyDesk',
        'ToDesk',
        'TeamViewer',
        'RustDesk',
        'Oray',
        'Sunlogin',
        'SunLogin'
    )

    foreach ($base in $baseDirs) {
        foreach ($vendor in $vendorDirs) {
            $candidate = Join-Path $base $vendor
            if (Test-Path -LiteralPath $candidate) {
                $roots.Add((Resolve-Path -LiteralPath $candidate).Path)
            }
        }
    }

    return $roots | Sort-Object -Unique
}

function Get-LogCandidateSnapshot {
    param([datetime]$Since)

    $roots = Get-RemoteToolRoots
    $items = New-Object System.Collections.Generic.List[object]
    $extensions = @('.log', '.txt', '.json', '.xml', '.ini', '.db')

    foreach ($root in $roots) {
        try {
            Get-ChildItem -LiteralPath $root -Recurse -File -ErrorAction Stop |
                Where-Object { $extensions -contains $_.Extension.ToLowerInvariant() } |
                Where-Object { $_.LastWriteTime -ge $Since } |
                Sort-Object LastWriteTime -Descending |
                Select-Object -First 300 |
                ForEach-Object {
                    $items.Add([pscustomobject]@{
                        full_name = $_.FullName
                        directory = $_.DirectoryName
                        name = $_.Name
                        extension = $_.Extension
                        length = $_.Length
                        last_write_time = $_.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss')
                    })
                }
        }
        catch {
            Add-CaptureError -Section "log_candidates:$root" -ErrorRecord $_
        }
    }

    return $items
}

function Save-LogTails {
    param(
        [Parameter(Mandatory = $true)]$LogCandidates,
        [Parameter(Mandatory = $true)][string]$SessionDir
    )

    $tailDir = Join-Path $SessionDir 'log_tails'
    New-Item -ItemType Directory -Force -Path $tailDir | Out-Null

    $index = New-Object System.Collections.Generic.List[object]
    $tailExtensions = @('.log', '.txt', '.json', '.xml', '.ini')
    foreach ($file in ($LogCandidates |
            Where-Object { $tailExtensions -contains ([string]$_.extension).ToLowerInvariant() } |
            Sort-Object last_write_time -Descending |
            Select-Object -First 80)) {
        try {
            $safeName = ($file.full_name -replace '^[A-Za-z]:', '' -replace '[\\/:*?"<>| ]+', '_').Trim('_')
            if ([string]::IsNullOrWhiteSpace($safeName)) {
                $safeName = [guid]::NewGuid().ToString('N')
            }
            $outPath = Join-Path $tailDir ($safeName + '.tail.txt')
            Get-Content -LiteralPath $file.full_name -Tail 200 -ErrorAction Stop |
                Set-Content -LiteralPath $outPath -Encoding UTF8

            $index.Add([pscustomobject]@{
                source = $file.full_name
                tail_file = $outPath
            })
        }
        catch {
            Add-CaptureError -Section "log_tail:$($file.full_name)" -ErrorRecord $_
        }
    }

    return $index
}

$capturedAt = Get-Date
$timestamp = $capturedAt.ToString('yyyyMMdd_HHmmss')
$sessionDir = Join-Path $OutputRoot "$timestamp-$Label"
New-Item -ItemType Directory -Force -Path $sessionDir | Out-Null

$since = $capturedAt.AddMinutes(-1 * $RecentMinutes)

$processes = @(Invoke-CaptureSection -Section 'processes' -ScriptBlock { Get-ProcessSnapshot })
$remoteProcesses = @($processes | Where-Object { $_.is_remote_candidate })

$windows = @(Invoke-CaptureSection -Section 'windows' -ScriptBlock { Get-WindowSnapshot })
$remoteWindows = @($windows | Where-Object { $_.is_remote_candidate })

$services = @(Invoke-CaptureSection -Section 'services' -ScriptBlock { Get-ServiceSnapshot })
$remoteServices = @($services | Where-Object { $_.is_remote_candidate })

$tcpConnections = @(Invoke-CaptureSection -Section 'tcp_connections' -ScriptBlock { Get-TcpConnectionSnapshot })
$remoteTcpConnections = @($tcpConnections | Where-Object { $_.is_remote_candidate })

$rdpEvents = @()
if (-not $SkipEventLogs) {
    $rdpEvents = @(Invoke-CaptureSection -Section 'rdp_events' -ScriptBlock { Get-RdpEventSnapshot -Since $since })
}

$logCandidates = @()
if (-not $SkipLogCandidates) {
    $logCandidates = @(Invoke-CaptureSection -Section 'log_candidates' -ScriptBlock { Get-LogCandidateSnapshot -Since $since })
}

$logTailIndex = @()
if ($IncludeLogContent -and $logCandidates.Count -gt 0) {
    $logTailIndex = @(Invoke-CaptureSection -Section 'log_tails' -ScriptBlock {
        Save-LogTails -LogCandidates $logCandidates -SessionDir $sessionDir
    })
}

$summary = [pscustomobject]@{
    label = $Label
    captured_at = $capturedAt.ToString('yyyy-MM-dd HH:mm:ss')
    recent_minutes = $RecentMinutes
    machine_name = $env:COMPUTERNAME
    user_name = $env:USERNAME
    is_admin = Get-IsAdmin
    output_dir = $sessionDir
    remote_process_count = $remoteProcesses.Count
    remote_window_count = $remoteWindows.Count
    remote_service_count = $remoteServices.Count
    remote_tcp_connection_count = $remoteTcpConnections.Count
    rdp_event_count = $rdpEvents.Count
    log_candidate_count = $logCandidates.Count
    errors = $script:CaptureErrors
}

Save-Json -Path (Join-Path $sessionDir 'summary.json') -Data $summary
Save-Json -Path (Join-Path $sessionDir 'processes.json') -Data $processes
Save-Json -Path (Join-Path $sessionDir 'remote_processes.json') -Data $remoteProcesses
Save-Json -Path (Join-Path $sessionDir 'windows.json') -Data $windows
Save-Json -Path (Join-Path $sessionDir 'remote_windows.json') -Data $remoteWindows
Save-Json -Path (Join-Path $sessionDir 'services.json') -Data $services
Save-Json -Path (Join-Path $sessionDir 'remote_services.json') -Data $remoteServices
Save-Json -Path (Join-Path $sessionDir 'tcp_connections.json') -Data $tcpConnections
Save-Json -Path (Join-Path $sessionDir 'remote_tcp_connections.json') -Data $remoteTcpConnections
Save-Json -Path (Join-Path $sessionDir 'rdp_events.json') -Data $rdpEvents
Save-Json -Path (Join-Path $sessionDir 'log_candidates.json') -Data $logCandidates
Save-Json -Path (Join-Path $sessionDir 'log_tails_index.json') -Data $logTailIndex

Set-Content -LiteralPath (Join-Path $sessionDir 'how_to_compare.txt') -Encoding UTF8 -Value @'
Take snapshots with consistent labels, then compare files across states.

Recommended labels per tool:
  <tool>_off
  <tool>_idle
  <tool>_window
  <tool>_connected
  <tool>_disconnected

Trust only signals that appear in the connected state and disappear after disconnect.
Process-only signals are weak because many remote tools keep background services running.
'@

Write-Host "Remote signal snapshot saved to:"
Write-Host $sessionDir
Write-Host ""
Write-Host "Key files:"
Write-Host "  summary.json"
Write-Host "  remote_processes.json"
Write-Host "  remote_windows.json"
Write-Host "  remote_services.json"
Write-Host "  remote_tcp_connections.json"
Write-Host "  rdp_events.json"
Write-Host "  log_candidates.json"
if ($IncludeLogContent) {
    Write-Host "  log_tails\\"
}
