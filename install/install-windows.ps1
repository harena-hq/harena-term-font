# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Jeeyong Um
param(
    [string]$From,
    [string]$Version
)

$ErrorActionPreference = 'Stop'

if ($From -and $Version) {
    Write-Error '--from and --version cannot be used together'
    exit 2
}

$destination = Join-Path $env:LOCALAPPDATA 'Microsoft\Windows\Fonts'
$registryKey = 'HKCU:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts'
New-Item -ItemType Directory -Force -Path $destination | Out-Null
New-Item -Path $registryKey -Force | Out-Null

$temporaryRoot = $null
try {
    if ($From) {
        if (-not (Test-Path -LiteralPath $From -PathType Container)) {
            Write-Error "source directory does not exist: $From"
            exit 1
        }
        $fontFiles = @(Get-ChildItem -LiteralPath $From -File -Filter '*.ttf')
    } else {
        $temporaryRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("HarenaTerm-" + [System.Guid]::NewGuid().ToString())
        New-Item -ItemType Directory -Force -Path $temporaryRoot | Out-Null
        $archive = Join-Path $temporaryRoot 'HarenaTerm-ttf.zip'
        $extractRoot = Join-Path $temporaryRoot 'extracted'
        if ($Version) {
            $url = "https://github.com/harena-hq/harena-term-font/releases/download/$Version/HarenaTerm-ttf.zip"
        } else {
            $url = 'https://github.com/harena-hq/harena-term-font/releases/latest/download/HarenaTerm-ttf.zip'
        }
        Invoke-WebRequest -Uri $url -OutFile $archive
        Expand-Archive -LiteralPath $archive -DestinationPath $extractRoot -Force
        $fontFiles = @(Get-ChildItem -LiteralPath $extractRoot -File -Filter '*.ttf' -Recurse)
    }

    if ($fontFiles.Count -eq 0) {
        Write-Error 'source contains no .ttf files'
        exit 1
    }

    $installed = 0
    foreach ($fontFile in $fontFiles) {
        $target = Join-Path $destination $fontFile.Name
        Copy-Item -LiteralPath $fontFile.FullName -Destination $target -Force
        $displayName = [System.IO.Path]::GetFileNameWithoutExtension($fontFile.Name)
        $displayName = $displayName -replace '([a-z])([A-Z])', '$1 $2'
        $displayName = $displayName -replace '-', ' '
        $valueName = "$displayName (TrueType)"
        New-ItemProperty -Path $registryKey -Name $valueName -Value $target -PropertyType String -Force | Out-Null
        Write-Output "installed $target"
        $installed++
    }
    Write-Output "Installed $installed fonts to $destination"
} finally {
    if ($temporaryRoot -and (Test-Path -LiteralPath $temporaryRoot)) {
        Remove-Item -LiteralPath $temporaryRoot -Recurse -Force
    }
}
