$ErrorActionPreference = 'Stop'

$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$assetDir = Join-Path $repoRoot 'src\Monitor.App\Assets'
New-Item -ItemType Directory -Path $assetDir -Force | Out-Null

Add-Type -AssemblyName System.Drawing

function New-RoundedRectPath([float]$x, [float]$y, [float]$w, [float]$h, [float]$r) {
    $path = New-Object System.Drawing.Drawing2D.GraphicsPath
    $d = $r * 2
    $path.AddArc($x, $y, $d, $d, 180, 90)
    $path.AddArc($x + $w - $d, $y, $d, $d, 270, 90)
    $path.AddArc($x + $w - $d, $y + $h - $d, $d, $d, 0, 90)
    $path.AddArc($x, $y + $h - $d, $d, $d, 90, 90)
    $path.CloseFigure()
    return $path
}

function Save-MonitorIconPng([int]$size, [string]$path) {
    $bmp = New-Object System.Drawing.Bitmap($size, $size, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $g.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
    $g.Clear([System.Drawing.Color]::Transparent)

    $scale = $size / 1024.0
    function S([double]$value) { return [single]($value * $scale) }

    $bg = New-RoundedRectPath (S 64) (S 64) (S 896) (S 896) (S 214)
    $rect = New-Object System.Drawing.RectangleF -ArgumentList (S 64), (S 64), (S 896), (S 896)
    $brush = New-Object System.Drawing.Drawing2D.LinearGradientBrush(
        $rect,
        [System.Drawing.Color]::FromArgb(255, 92, 141, 255),
        [System.Drawing.Color]::FromArgb(255, 13, 78, 216),
        55
    )
    $g.FillPath($brush, $bg)

    $shine = New-Object System.Drawing.Drawing2D.GraphicsPath
    $shine.AddBezier((S 216),(S 152),(S 352),(S 96),(S 646),(S 102),(S 794),(S 226))
    $shine.AddBezier((S 660),(S 176),(S 400),(S 168),(S 238),(S 262),(S 214),(S 231))
    $shine.AddBezier((S 205),(S 188),(S 205),(S 170),(S 216),(S 152),(S 216),(S 152))
    $shine.CloseFigure()
    $shineBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(58, 255, 255, 255))
    $g.FillPath($shineBrush, $shine)

    $white = [System.Drawing.Color]::FromArgb(248, 251, 255)
    $pen = New-Object System.Drawing.Pen -ArgumentList $white, ([single][Math]::Max(2, (48 * $scale)))
    $pen.StartCap = [System.Drawing.Drawing2D.LineCap]::Round
    $pen.EndCap = [System.Drawing.Drawing2D.LineCap]::Round
    $monitor = New-RoundedRectPath (S 266) (S 278) (S 492) (S 326) (S 56)
    $g.DrawPath($pen, $monitor)
    $g.DrawLine($pen, (S 512), (S 620), (S 512), (S 718))
    $g.DrawLine($pen, (S 398), (S 746), (S 626), (S 746))

    $halo = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(255, 234, 253, 245))
    $green = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(255, 20, 167, 108))
    $glint = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(160, 255, 255, 255))
    $g.FillEllipse($halo, (S 646), (S 218), (S 172), (S 172))
    $g.FillEllipse($green, (S 680), (S 252), (S 104), (S 104))
    $g.FillEllipse($glint, (S 696), (S 266), (S 32), (S 32))

    $bmp.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
    $g.Dispose()
    $bmp.Dispose()
}

function Write-Ico([string[]]$pngPaths, [string]$icoPath) {
    $images = @()
    foreach ($pngPath in $pngPaths) {
        $bytes = [System.IO.File]::ReadAllBytes($pngPath)
        $name = [System.IO.Path]::GetFileNameWithoutExtension($pngPath)
        $size = [int]($name -replace '[^0-9]', '')
        $images += [pscustomobject]@{ Size = $size; Bytes = $bytes }
    }

    $stream = [System.IO.File]::Create($icoPath)
    $writer = New-Object System.IO.BinaryWriter($stream)
    $writer.Write([UInt16]0)
    $writer.Write([UInt16]1)
    $writer.Write([UInt16]$images.Count)

    $offset = 6 + (16 * $images.Count)
    foreach ($image in $images) {
        $entrySize = if ($image.Size -ge 256) { 0 } else { $image.Size }
        $writer.Write([byte]$entrySize)
        $writer.Write([byte]$entrySize)
        $writer.Write([byte]0)
        $writer.Write([byte]0)
        $writer.Write([UInt16]1)
        $writer.Write([UInt16]32)
        $writer.Write([UInt32]$image.Bytes.Length)
        $writer.Write([UInt32]$offset)
        $offset += $image.Bytes.Length
    }

    foreach ($image in $images) {
        $writer.Write($image.Bytes)
    }

    $writer.Dispose()
    $stream.Dispose()
}

$sizes = @(16, 24, 32, 48, 64, 128, 256)
$pngPaths = @()
foreach ($size in $sizes) {
    $pngPath = Join-Path $assetDir ("monitor-icon-{0}.png" -f $size)
    Save-MonitorIconPng $size $pngPath
    $pngPaths += $pngPath
}

Copy-Item -LiteralPath (Join-Path $assetDir 'monitor-icon-256.png') -Destination (Join-Path $assetDir 'monitor-icon.png') -Force
Write-Ico $pngPaths (Join-Path $assetDir 'monitor-icon.ico')

Write-Output "Generated icon assets in $assetDir"
