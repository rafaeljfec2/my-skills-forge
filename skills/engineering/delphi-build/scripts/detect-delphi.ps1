[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

function Find-DelphiInstallation {
    $registryBases = @(
        "HKCU:\Software\Embarcadero\BDS",
        "HKLM:\Software\Embarcadero\BDS",
        "HKLM:\Software\WOW6432Node\Embarcadero\BDS"
    )

    $installations = @()

    foreach ($base in $registryBases) {
        if (-not (Test-Path $base)) { continue }

        Get-ChildItem $base | ForEach-Object {
            $versionKey = $_.PSChildName
            $regPath = "$base\$versionKey"

            try {
                $rootDir = (Get-ItemProperty -Path $regPath -Name "RootDir" -ErrorAction SilentlyContinue).RootDir
                if (-not $rootDir) { return }

                $dcc32 = Join-Path $rootDir "bin\dcc32.exe"
                $dcc64 = Join-Path $rootDir "bin\dcc64.exe"
                $brcc32 = Join-Path $rootDir "bin\brcc32.exe"
                $cgrc = Join-Path $rootDir "bin\cgrc.exe"
                $rsvars = Join-Path $rootDir "bin\rsvars.bat"

                if (-not (Test-Path $dcc32)) { return }

                $versionOutput = & $dcc32 --version 2>&1 | Select-Object -First 1

                $libPathWin32 = ""
                $libPathKey = "$regPath\Library\Win32"
                if (Test-Path $libPathKey) {
                    $libPathWin32 = (Get-ItemProperty -Path $libPathKey -Name "Search Path" -ErrorAction SilentlyContinue)."Search Path"
                }

                $browsingPath = ""
                if (Test-Path $libPathKey) {
                    $browsingPath = (Get-ItemProperty -Path $libPathKey -Name "Browsing Path" -ErrorAction SilentlyContinue)."Browsing Path"
                }

                $envVars = @{}
                $envVarsKey = "$regPath\Environment Variables"
                if (Test-Path $envVarsKey) {
                    $props = Get-ItemProperty -Path $envVarsKey -ErrorAction SilentlyContinue
                    $props.PSObject.Properties | Where-Object {
                        $_.Name -notmatch "^PS" -and $_.Name -notmatch "^(PSChildName|PSDrive|PSProvider|PSPath|PSParentPath)"
                    } | ForEach-Object {
                        $envVars[$_.Name] = $_.Value
                    }
                }

                $installations += [PSCustomObject]@{
                    Version            = $versionKey
                    RootDir            = $rootDir
                    DCC32              = $dcc32
                    DCC64              = if (Test-Path $dcc64) { $dcc64 } else { $null }
                    BRCC32             = if (Test-Path $brcc32) { $brcc32 } else { $null }
                    CGRC               = if (Test-Path $cgrc) { $cgrc } else { $null }
                    RsVars             = if (Test-Path $rsvars) { $rsvars } else { $null }
                    VersionOutput      = $versionOutput
                    LibrarySearchPath  = $libPathWin32
                    BrowsingPath       = $browsingPath
                    EnvironmentVars    = $envVars
                    RegistryPath       = $regPath
                }
            } catch {}
        }
    }

    return $installations
}

function Expand-DelphiVars {
    param(
        [string]$Value,
        [hashtable]$Vars
    )

    $result = $Value
    $maxIterations = 5
    for ($i = 0; $i -lt $maxIterations; $i++) {
        $previous = $result
        foreach ($key in $Vars.Keys) {
            $result = $result -replace [regex]::Escape("`$($key)"), $Vars[$key]
        }
        if ($result -eq $previous) { break }
    }

    return $result
}

$installations = Find-DelphiInstallation

if ($installations.Count -eq 0) {
    $fallbackPaths = @(
        "C:\Program Files (x86)\Embarcadero\Studio",
        "C:\Program Files\Embarcadero\Studio"
    )

    foreach ($fallback in $fallbackPaths) {
        if (-not (Test-Path $fallback)) { continue }
        Get-ChildItem $fallback -Directory | ForEach-Object {
            $dcc32 = Join-Path $_.FullName "bin\dcc32.exe"
            if (Test-Path $dcc32) {
                $installations += [PSCustomObject]@{
                    Version            = $_.Name
                    RootDir            = $_.FullName
                    DCC32              = $dcc32
                    DCC64              = $null
                    BRCC32             = $null
                    CGRC               = $null
                    RsVars             = $null
                    VersionOutput      = ""
                    LibrarySearchPath  = ""
                    BrowsingPath       = ""
                    EnvironmentVars    = @{}
                    RegistryPath       = ""
                }
            }
        }
    }
}

if ($installations.Count -eq 0) {
    Write-Error "No Delphi/RAD Studio installation found."
    exit 1
}

$latest = $installations | Sort-Object {
    $priority = if ($_.RegistryPath -like "HKCU:*") { 1 } else { 0 }
    [double]$_.Version * 10 + $priority
} -Descending | Select-Object -First 1

$bds = $latest.RootDir.TrimEnd('\', '/')
$bdsCommon = Join-Path ([Environment]::GetFolderPath("CommonDocuments")) "Embarcadero\Studio\$($latest.Version)"

$bdsUserDir = Join-Path ([Environment]::GetFolderPath("MyDocuments")) "Embarcadero\Studio\$($latest.Version)"

$vars = @{
    "BDS"          = $bds
    "BDSLIB"       = "$bds\lib"
    "BDSBIN"       = "$bds\bin"
    "BDSINCLUDE"   = "$bds\include"
    "BDSCOMMONDIR" = $bdsCommon
    "BDSUSERDIR"   = $bdsUserDir
    "Platform"     = "Win32"
    "Config"       = "Debug"
}

if ($latest.EnvironmentVars) {
    foreach ($key in $latest.EnvironmentVars.Keys) {
        $vars[$key] = Expand-DelphiVars -Value $latest.EnvironmentVars[$key] -Vars $vars
    }
}

$expandedLibPath = ""
if ($latest.LibrarySearchPath) {
    $segments = $latest.LibrarySearchPath -split ";"
    $expanded = $segments | ForEach-Object {
        $seg = Expand-DelphiVars -Value $_ -Vars $vars
        $seg.Trim()
    } | Where-Object { $_ -ne "" }
    $expandedLibPath = $expanded -join ";"
}

$output = [ordered]@{
    Version            = $latest.Version
    VersionOutput      = $latest.VersionOutput
    RootDir            = $bds
    DCC32              = $latest.DCC32
    DCC64              = $latest.DCC64
    BRCC32             = $latest.BRCC32
    CGRC               = $latest.CGRC
    RsVars             = $latest.RsVars
    LibrarySearchPath  = $expandedLibPath
    EnvironmentVars    = $latest.EnvironmentVars
    BDSCommonDir       = $bdsCommon
    TotalInstallations = $installations.Count
}

$output | ConvertTo-Json -Depth 3
