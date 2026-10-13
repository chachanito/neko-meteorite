param(
    [string]$RigDir = (Join-Path $PSScriptRoot '..\assets\fox-rig-v3'),
    [int]$FrameCount = 50,
    [int]$CanvasSize = 768
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing

function Get-AlphaBounds {
    param([System.Drawing.Bitmap]$Bitmap)

    $rect = [System.Drawing.Rectangle]::new(0, 0, $Bitmap.Width, $Bitmap.Height)
    $data = $Bitmap.LockBits(
        $rect,
        [System.Drawing.Imaging.ImageLockMode]::ReadOnly,
        [System.Drawing.Imaging.PixelFormat]::Format32bppArgb
    )

    try {
        $stride = [Math]::Abs($data.Stride)
        $bytes = [byte[]]::new($stride * $Bitmap.Height)
        [Runtime.InteropServices.Marshal]::Copy($data.Scan0, $bytes, 0, $bytes.Length)

        $minX = $Bitmap.Width
        $minY = $Bitmap.Height
        $maxX = -1
        $maxY = -1

        for ($y = 0; $y -lt $Bitmap.Height; $y++) {
            $row = $y * $stride
            for ($x = 0; $x -lt $Bitmap.Width; $x++) {
                if ($bytes[$row + ($x * 4) + 3] -gt 8) {
                    if ($x -lt $minX) { $minX = $x }
                    if ($x -gt $maxX) { $maxX = $x }
                    if ($y -lt $minY) { $minY = $y }
                    if ($y -gt $maxY) { $maxY = $y }
                }
            }
        }

        if ($maxX -lt 0) { return $rect }
        return [System.Drawing.Rectangle]::new($minX, $minY, $maxX - $minX + 1, $maxY - $minY + 1)
    }
    finally {
        $Bitmap.UnlockBits($data)
    }
}

function Import-CroppedBitmap {
    param([string]$Path)

    $source = [System.Drawing.Bitmap]::FromFile($Path)
    try {
        $bounds = Get-AlphaBounds -Bitmap $source
        $cropped = [System.Drawing.Bitmap]::new(
            $bounds.Width,
            $bounds.Height,
            [System.Drawing.Imaging.PixelFormat]::Format32bppArgb
        )
        $graphics = [System.Drawing.Graphics]::FromImage($cropped)
        try {
            $graphics.Clear([System.Drawing.Color]::Transparent)
            $graphics.CompositingMode = [System.Drawing.Drawing2D.CompositingMode]::SourceCopy
            $graphics.DrawImage(
                $source,
                [System.Drawing.Rectangle]::new(0, 0, $bounds.Width, $bounds.Height),
                $bounds,
                [System.Drawing.GraphicsUnit]::Pixel
            )
        }
        finally {
            $graphics.Dispose()
        }
        return $cropped
    }
    finally {
        $source.Dispose()
    }
}

function Draw-Layer {
    param(
        [System.Drawing.Graphics]$Graphics,
        [System.Drawing.Bitmap]$Image,
        [float]$X,
        [float]$Y,
        [float]$Width,
        [float]$Angle,
        [float]$PivotX,
        [float]$PivotY,
        [float]$ScaleX = 1,
        [float]$ScaleY = 1
    )

    $height = $Width * $Image.Height / $Image.Width
    $worldPivotX = $X + ($Width * $PivotX)
    $worldPivotY = $Y + ($height * $PivotY)
    $state = $Graphics.Save()
    try {
        $Graphics.TranslateTransform($worldPivotX, $worldPivotY)
        $Graphics.RotateTransform($Angle)
        $Graphics.ScaleTransform($ScaleX, $ScaleY)
        $Graphics.TranslateTransform(-$worldPivotX, -$worldPivotY)
        $Graphics.DrawImage($Image, $X, $Y, $Width, $height)
    }
    finally {
        $Graphics.Restore($state)
    }
}

$rigPath = [IO.Path]::GetFullPath($RigDir)
$frameDir = Join-Path $rigPath 'frames'
[IO.Directory]::CreateDirectory($frameDir) | Out-Null

$body = Import-CroppedBitmap -Path (Join-Path $rigPath 'fox-body.png')
$head = Import-CroppedBitmap -Path (Join-Path $rigPath 'fox-head.png')
$tail = Import-CroppedBitmap -Path (Join-Path $rigPath 'fox-tail-corrected.png')

try {
    $manifestFrames = @()

    for ($index = 0; $index -lt $FrameCount; $index++) {
        $phase = 2 * [Math]::PI * $index / $FrameCount
        $breath = ([Math]::Cos($phase) + 1) / 2
        $bodySway = [Math]::Sin($phase)
        $headBeat = [Math]::Sin((2 * $phase) - 0.35)
        $tailWave = [Math]::Sin((2 * $phase) - 0.6)

        $frame = [System.Drawing.Bitmap]::new(
            $CanvasSize,
            $CanvasSize,
            [System.Drawing.Imaging.PixelFormat]::Format32bppArgb
        )
        $graphics = [System.Drawing.Graphics]::FromImage($frame)

        try {
            $graphics.Clear([System.Drawing.Color]::Transparent)
            $graphics.CompositingMode = [System.Drawing.Drawing2D.CompositingMode]::SourceOver
            $graphics.CompositingQuality = [System.Drawing.Drawing2D.CompositingQuality]::HighQuality
            $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
            $graphics.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
            $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality

            $bodyWidth = 406.0
            $bodyX = (($CanvasSize - $bodyWidth) / 2) + (2.2 * $bodySway)
            $bodyY = 330.0 - (3.2 * $breath)
            $bodyAngle = 0.75 * $bodySway
            $bodyScaleX = 1 + (0.006 * $breath)
            $bodyScaleY = 1 + (0.014 * $breath)

            $tailWidth = 300.0
            $tailX = 372.0 + (0.8 * $bodySway)
            $tailY = 584.0 - (1.0 * $breath)
            $tailAngle = -7 + (8 * $tailWave)

            $headWidth = 374.0
            $headX = (($CanvasSize - $headWidth) / 2) + (5.2 * $bodySway)
            $headY = 94.0 - (5.5 * $breath) + (2.2 * $headBeat)
            $headAngle = (2.6 * $bodySway) + (0.8 * $headBeat)
            $headScale = 1 + (0.006 * $headBeat)

            Draw-Layer -Graphics $graphics -Image $tail -X $tailX -Y $tailY -Width $tailWidth `
                -Angle $tailAngle -PivotX 0.02 -PivotY 0.34
            Draw-Layer -Graphics $graphics -Image $body -X $bodyX -Y $bodyY -Width $bodyWidth `
                -Angle $bodyAngle -PivotX 0.5 -PivotY 0.91 -ScaleX $bodyScaleX -ScaleY $bodyScaleY
            Draw-Layer -Graphics $graphics -Image $head -X $headX -Y $headY -Width $headWidth `
                -Angle $headAngle -PivotX 0.5 -PivotY 0.9 -ScaleX $headScale -ScaleY $headScale
        }
        finally {
            $graphics.Dispose()
        }

        $fileName = 'fox-{0:D3}.png' -f $index
        $outputPath = Join-Path $frameDir $fileName
        $frame.Save($outputPath, [System.Drawing.Imaging.ImageFormat]::Png)
        $frame.Dispose()
        $manifestFrames += "assets/fox-rig-v3/frames/$fileName"
    }

    $manifest = [ordered]@{
        frameCount = $FrameCount
        fps = 12
        loopDurationSeconds = [Math]::Round($FrameCount / 12, 3)
        width = $CanvasSize
        height = $CanvasSize
        frames = $manifestFrames
    }
    $manifest | ConvertTo-Json -Depth 4 | Set-Content -Encoding utf8 (Join-Path $rigPath 'manifest.json')
}
finally {
    $body.Dispose()
    $head.Dispose()
    $tail.Dispose()
}

Write-Output "Created $FrameCount frames in $frameDir"
