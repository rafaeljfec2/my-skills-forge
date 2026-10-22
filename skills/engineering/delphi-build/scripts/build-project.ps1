[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$DCC32,
    [Parameter(Mandatory)][string]$ProjectDir,
    [Parameter(Mandatory)][string]$DprFile,
    [ValidateSet("Debug", "Release")][string]$Config = "Debug",
    [string]$LibrarySearchPath = "",
    [string]$ExtraSearchPaths = "",
    [string]$OutputDir = "",
    [string]$DCUOutputDir = "",
    [string]$ObjOutputDir = "",
    [string]$BRCC32 = "",
    [string]$RsVars = "",
    [string]$DprojFile = "",
    [string]$NamespacePrefix = "Winapi;System.Win;Data.Win;Datasnap.Win;Web.Win;Soap.Win;Xml.Win;Bde;System;Xml;Data;Datasnap;Web;Soap;Vcl;Vcl.Imaging;Vcl.Touch;Vcl.Samples;Vcl.Shell;Frx;frxClass",
    [string]$BDS = "",
    [string]$BDSCommonDir = "",
    [switch]$KeepCfg,
    [switch]$Use64Bit,
    [switch]$RegenerateRes
)

$ErrorActionPreference = 'Stop'

$projectName = [System.IO.Path]::GetFileNameWithoutExtension($DprFile)
$dprFullPath = Join-Path $ProjectDir $DprFile
$cfgPath = Join-Path $ProjectDir "$projectName.cfg"

if (-not (Test-Path $dprFullPath)) {
    Write-Error "Project file not found: $dprFullPath"
    exit 1
}

if (-not $DprojFile) {
    $dprojCandidate = Join-Path $ProjectDir "$projectName.dproj"
    if (Test-Path $dprojCandidate) { $DprojFile = $dprojCandidate }
}

# Output dirs and dproj parsing are resolved after function definitions (see below)

function Resolve-ShortPath {
    param([string]$Path)

    if ($Path -match '[^\x00-\x7F]') {
        $segments = $Path -split '\\'
        $rebuilt = ""
        foreach ($seg in $segments) {
            if ($rebuilt -eq "") {
                $rebuilt = $seg
                continue
            }
            $candidate = Join-Path $rebuilt $seg
            if ($seg -match '[^\x00-\x7F]' -and (Test-Path $rebuilt)) {
                try {
                    $dirOutput = cmd /c "dir /x ""$rebuilt"" 2>nul" | Where-Object { $_ -match [regex]::Escape($seg) }
                    if ($dirOutput -match '\s(\S+~\d)\s') {
                        $rebuilt = Join-Path $rebuilt $Matches[1]
                        continue
                    }
                } catch {}
            }
            $rebuilt = $candidate
        }
        return $rebuilt
    }
    return $Path
}

function Expand-DprojVars {
    param([string]$Value)

    $result = $Value

    $varMap = @{}
    if ($BDS) { $varMap['$(BDS)'] = $BDS }
    if ($BDSCommonDir) {
        $varMap['$(BDSCOMMONDIR)'] = $BDSCommonDir
        $varMap['$(BDSLIB)'] = "$BDS\lib"
    }
    $varMap['$(Platform)'] = 'Win32'
    $varMap['$(Config)'] = $Config
    $varMap['$(ProjectDir)'] = "$ProjectDir\"

    foreach ($key in $varMap.Keys) {
        $result = $result -replace [regex]::Escape($key), $varMap[$key]
    }

    $result = [Environment]::ExpandEnvironmentVariables($result)
    return $result
}

function Get-DprojPropertyGroups {
    if (-not $DprojFile -or -not (Test-Path $DprojFile)) { return $null }

    try {
        [xml]$xml = Get-Content $DprojFile -Encoding UTF8

        $ns = New-Object Xml.XmlNamespaceManager($xml.NameTable)
        $defaultNs = $xml.DocumentElement.NamespaceURI
        if ($defaultNs) { $ns.AddNamespace("msbuild", $defaultNs) }

        $propGroups = if ($defaultNs) {
            $xml.SelectNodes("//msbuild:PropertyGroup", $ns)
        } else {
            $xml.SelectNodes("//PropertyGroup")
        }

        $cfgNum = if ($Config -eq "Debug") { "2" } else { "1" }

        $groups = @{
            Base          = $null
            Base_Win32    = $null
            Cfg           = $null
            Cfg_Win32     = $null
        }

        foreach ($pg in $propGroups) {
            $cond = $pg.GetAttribute("Condition")
            if (-not $cond) { continue }

            if ($cond -match "'\$\(Base\)'!=''") {
                if ($cond -notmatch "Win32|Win64|Cfg") { $groups.Base = $pg }
            }
            if ($cond -match "'\$\(Base_Win32\)'!=''") { $groups.Base_Win32 = $pg }
            if ($cond -match "'\$\(Cfg_$cfgNum\)'!=''") {
                if ($cond -notmatch "Win32|Win64") { $groups.Cfg = $pg }
            }
            if ($cond -match "'\$\(Cfg_${cfgNum}_Win32\)'!=''") { $groups.Cfg_Win32 = $pg }
        }

        return $groups
    } catch {
        Write-Warning "Could not parse .dproj: $_"
        return $null
    }
}

function Get-DprojProperty {
    param(
        [hashtable]$Groups,
        [string]$PropertyName
    )

    if (-not $Groups) { return $null }

    $searchOrder = @("Cfg_Win32", "Cfg", "Base_Win32", "Base")
    foreach ($key in $searchOrder) {
        $pg = $Groups[$key]
        if (-not $pg) { continue }
        $node = $pg[$PropertyName]
        if ($node -and $node.InnerText) {
            return $node.InnerText
        }
    }
    return $null
}

function Extract-DprojOutputPaths {
    param([hashtable]$Groups)

    if (-not $Groups) { return }

    $exeOut = Get-DprojProperty -Groups $Groups -PropertyName "DCC_ExeOutput"
    $dcuOut = Get-DprojProperty -Groups $Groups -PropertyName "DCC_DcuOutput"
    $objOut = Get-DprojProperty -Groups $Groups -PropertyName "DCC_ObjOutput"
    $dcpOut = Get-DprojProperty -Groups $Groups -PropertyName "DCC_DcpOutput"

    if ($exeOut) {
        $expanded = Expand-DprojVars -Value $exeOut
        if (-not [System.IO.Path]::IsPathRooted($expanded)) {
            $expanded = Join-Path $ProjectDir $expanded
        }
        $expanded = [System.IO.Path]::GetFullPath($expanded)
        if (-not $script:OutputDir) { $script:OutputDir = $expanded }
        Write-Host "[DPROJ] ExeOutput: $expanded" -ForegroundColor DarkCyan
    }

    if ($dcuOut) {
        $expanded = Expand-DprojVars -Value $dcuOut
        if (-not [System.IO.Path]::IsPathRooted($expanded)) {
            $expanded = Join-Path $ProjectDir $expanded
        }
        $expanded = [System.IO.Path]::GetFullPath($expanded)
        if (-not $script:DCUOutputDir) { $script:DCUOutputDir = $expanded }
        Write-Host "[DPROJ] DcuOutput: $expanded" -ForegroundColor DarkCyan
    }

    if ($objOut) {
        $expanded = Expand-DprojVars -Value $objOut
        if (-not [System.IO.Path]::IsPathRooted($expanded)) {
            $expanded = Join-Path $ProjectDir $expanded
        }
        $expanded = [System.IO.Path]::GetFullPath($expanded)
        if (-not $script:ObjOutputDir) { $script:ObjOutputDir = $expanded }
    }
}

function Extract-DprojSearchPaths {
    param([hashtable]$Groups)

    if (-not $Groups) { return @() }

    try {
        $paths = @()
        $searchPathProps = @("DCC_UnitSearchPath", "DCC_IncludePath", "DCC_ResourcePath")
        $searchOrder = @("Base", "Base_Win32", "Cfg", "Cfg_Win32")

        foreach ($key in $searchOrder) {
            $pg = $Groups[$key]
            if (-not $pg) { continue }

            foreach ($propName in $searchPathProps) {
                $node = $pg[$propName]
                if ($node -and $node.InnerText) {
                    $segments = $node.InnerText -split ";"
                    foreach ($seg in $segments) {
                        $trimmed = $seg.Trim()
                        if ($trimmed -eq "" -or $trimmed -match '^\$\(DCC_') { continue }
                        $expanded = Expand-DprojVars -Value $trimmed
                        if ($expanded -and $expanded -ne "") { $paths += $expanded }
                    }
                }
            }
        }

        $nsSegments = @()
        $nsKeys = @("Cfg_Win32", "Cfg", "Base_Win32", "Base")
        foreach ($key in $nsKeys) {
            $pg = $Groups[$key]
            if (-not $pg) { continue }
            $n = $pg["DCC_Namespace"]
            if ($n -and $n.InnerText) {
                $parts = $n.InnerText -split ";" | ForEach-Object { $_.Trim() } | Where-Object {
                    $_ -ne "" -and $_ -notmatch '^\$\('
                }
                $nsSegments += $parts
            }
        }
        if ($nsSegments.Count -gt 0) {
            $script:NamespacePrefix = ($nsSegments | Select-Object -Unique) -join ";"
        }

        return $paths | Select-Object -Unique
    } catch {
        Write-Warning "Could not extract search paths from .dproj: $_"
        return @()
    }
}

function Build-SearchPaths {
    $allPaths = @()

    $dprojPaths = Extract-DprojSearchPaths -Groups $dprojGroups
    if ($dprojPaths.Count -gt 0) {
        Write-Host "[INFO] Extracted $($dprojPaths.Count) paths from .dproj" -ForegroundColor DarkCyan
        $allPaths += $dprojPaths
    }

    if ($LibrarySearchPath) {
        $allPaths += $LibrarySearchPath -split ";" | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne "" }
    }

    if ($ExtraSearchPaths) {
        $allPaths += $ExtraSearchPaths -split ";" | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne "" }
    }

    $resolved = @()
    foreach ($p in $allPaths) {
        $expanded = [Environment]::ExpandEnvironmentVariables($p)
        $short = Resolve-ShortPath -Path $expanded
        $resolved += $short
    }

    $unique = $resolved | Select-Object -Unique

    $dcuFirst = @()
    $sourceOnly = @()

    foreach ($dir in $unique) {
        if (-not (Test-Path $dir -ErrorAction SilentlyContinue)) { continue }

        $hasDcu = (Get-ChildItem -Path $dir -Filter "*.dcu" -ErrorAction SilentlyContinue | Select-Object -First 1) -ne $null
        $hasDcp = (Get-ChildItem -Path $dir -Filter "*.dcp" -ErrorAction SilentlyContinue | Select-Object -First 1) -ne $null

        if ($hasDcu -or $hasDcp) {
            $dcuFirst += $dir
        } else {
            $sourceOnly += $dir
        }
    }

    Write-Host "[INFO] Path priority: $($dcuFirst.Count) DCU-dirs first, $($sourceOnly.Count) source-dirs second" -ForegroundColor DarkCyan
    return @($dcuFirst) + @($sourceOnly)
}

function Build-CfgContent {
    param(
        [string[]]$SearchPaths,
        [string[]]$ResourceOnlyPaths = @()
    )

    $lines = @()

    if ($Config -eq "Debug") {
        $lines += '-$O-'
        $lines += '-$W+'
        $lines += '-$R+'
        $lines += '-$Q+'
        $lines += '-$C+'
        $lines += '-$D+'
        $lines += '-$L+'
        $lines += '-$Y+'
        $lines += '-V'
        $lines += '-VN'
        $lines += '-DDEBUG'
    } else {
        $lines += '-$O+'
        $lines += '-$W-'
        $lines += '-$R-'
        $lines += '-$Q-'
        $lines += '-$C-'
        $lines += '-$D-'
        $lines += '-$L-'
        $lines += '-$Y-'
        $lines += '-DRELEASE'
    }

    $lines += '-$M-'
    $lines += '-$H+'
    $lines += '-$J-'
    $lines += '-$B-'
    $lines += '-$X+'

    $lines += "-AGenerics.Collections=System.Generics.Collections"
    $lines += "-AGenerics.Defaults=System.Generics.Defaults"
    $lines += "-AWinTypes=Winapi.Windows"
    $lines += "-AWinProcs=Winapi.Windows"

    if ($NamespacePrefix) {
        $lines += "-NS$NamespacePrefix"
    }

    $safeOutputDir = $OutputDir.TrimEnd('\', '/')
    $safeDCUOutputDir = $DCUOutputDir.TrimEnd('\', '/')

    $lines += "-E""$safeOutputDir"""
    $lines += "-NU""$safeDCUOutputDir"""
    $lines += "-NO""$safeDCUOutputDir"""
    $lines += "-N0""$safeDCUOutputDir"""
    $lines += "-U""$safeDCUOutputDir"""
    $lines += "-I""$safeDCUOutputDir"""

    foreach ($sp in $SearchPaths) {
        if (Test-Path $sp -ErrorAction SilentlyContinue) {
            $lines += "-U""$sp"""
            $lines += "-I""$sp"""
            $lines += "-R""$sp"""
        }
    }

    foreach ($rp in $ResourceOnlyPaths) {
        if (Test-Path $rp -ErrorAction SilentlyContinue) {
            $lines += "-R""$rp"""
            $lines += "-I""$rp"""
        }
    }

    return $lines -join "`r`n"
}

function Get-VersionInfoFromDproj {
    param([hashtable]$Groups)

    if (-not $Groups) { return $null }

    $major  = Get-DprojProperty -Groups $Groups -PropertyName "VerInfo_MajorVer"
    $minor  = Get-DprojProperty -Groups $Groups -PropertyName "VerInfo_MinorVer"
    $release = Get-DprojProperty -Groups $Groups -PropertyName "VerInfo_Release"
    $build  = Get-DprojProperty -Groups $Groups -PropertyName "VerInfo_Build"
    $locale = Get-DprojProperty -Groups $Groups -PropertyName "VerInfo_Locale"
    $keysRaw = Get-DprojProperty -Groups $Groups -PropertyName "VerInfo_Keys"
    $iconRaw = Get-DprojProperty -Groups $Groups -PropertyName "Icon_MainIcon"

    if (-not $major) { $major = "1" }
    if (-not $minor) { $minor = "0" }
    if (-not $release) { $release = "0" }
    if (-not $build) { $build = "0" }
    if (-not $locale) { $locale = "1033" }

    $keys = @{}
    if ($keysRaw) {
        $keysRaw -split ";" | ForEach-Object {
            $parts = $_ -split "=", 2
            if ($parts.Count -eq 2) {
                $val = $parts[1] -replace '\$\(MSBuildProjectName\)', $projectName
                $keys[$parts[0]] = $val
            }
        }
    }

    return @{
        Major   = [int]$major
        Minor   = [int]$minor
        Release = [int]$release
        Build   = [int]$build
        Locale  = [int]$locale
        Keys    = $keys
        Icon    = $iconRaw
    }
}

function Build-VersionInfoRc {
    param([hashtable]$VerInfo)

    $maj = $VerInfo.Major; $min = $VerInfo.Minor; $rel = $VerInfo.Release; $bld = $VerInfo.Build
    $localeHex = "0x{0:X4}" -f $VerInfo.Locale
    $codepage = 1252
    $blockId = "{0:X4}{1:X4}" -f $VerInfo.Locale, $codepage

    $k = $VerInfo.Keys
    $fileVer = if ($k["FileVersion"]) { $k["FileVersion"] } else { "$maj.$min.$rel.$bld" }
    $prodVer = if ($k["ProductVersion"]) { $k["ProductVersion"] } else { "$maj.$min.$rel.$bld" }

    $prodVerParts = $prodVer -split "\."
    while ($prodVerParts.Count -lt 4) { $prodVerParts += "0" }

    $stringValues = @(
        "CompanyName", "FileDescription", "FileVersion", "InternalName",
        "LegalCopyright", "LegalTrademarks", "OriginalFilename",
        "ProductName", "ProductVersion", "Comments"
    )

    $stringBlock = ""
    foreach ($sv in $stringValues) {
        $val = if ($k[$sv]) { $k[$sv] } else { "" }
        $stringBlock += "            VALUE ""$sv"", ""$val\0""`r`n"
    }

    $rc = @"
1 VERSIONINFO
FILEVERSION $maj,$min,$rel,$bld
PRODUCTVERSION $($prodVerParts[0]),$($prodVerParts[1]),$($prodVerParts[2]),$($prodVerParts[3])
FILEFLAGSMASK 0x3fL
FILEFLAGS 0x0L
FILEOS 0x40004L
FILETYPE 0x1L
FILESUBTYPE 0x0L
BEGIN
    BLOCK "StringFileInfo"
    BEGIN
        BLOCK "$blockId"
        BEGIN
$stringBlock        END
    END
    BLOCK "VarFileInfo"
    BEGIN
        VALUE "Translation", $localeHex, $codepage
    END
END
"@
    return $rc
}

function Ensure-ResFile {
    $resFile = Join-Path $ProjectDir "$projectName.res"

    if ($RegenerateRes) {
        Write-Host "[BUILD] RegenerateRes: building full .res (version + icon)..." -ForegroundColor Yellow

        $verInfo = Get-VersionInfoFromDproj -Groups $dprojGroups
        if ($verInfo) {
            $rcPath = Join-Path $ProjectDir "$projectName`_build.rc"
            $rcContent = Build-VersionInfoRc -VerInfo $verInfo

            $iconFile = $null
            if ($verInfo.Icon) {
                $iconCandidate = Join-Path $ProjectDir $verInfo.Icon
                if (Test-Path $iconCandidate) {
                    $iconFile = $verInfo.Icon
                }
            }

            if ($iconFile) {
                $rcContent += "`r`nMAINICON ICON ""$iconFile""`r`n"
                Write-Host "[BUILD] Including icon: $iconFile" -ForegroundColor DarkCyan
            } else {
                Write-Host "[BUILD] No .ico file found, generating version-only .res" -ForegroundColor Yellow
            }

            [System.IO.File]::WriteAllText($rcPath, $rcContent, [System.Text.Encoding]::GetEncoding(1252))

            if ($BRCC32 -and (Test-Path $BRCC32)) {
                Remove-Item $resFile -Force -ErrorAction SilentlyContinue
                $brccOutput = & $BRCC32 -fo"$resFile" $rcPath 2>&1 | Out-String
                Remove-Item $rcPath -Force -ErrorAction SilentlyContinue

                if (Test-Path $resFile) {
                    $v = "$($verInfo.Major).$($verInfo.Minor).$($verInfo.Release).$($verInfo.Build)"
                    Write-Host "[OK] Generated $projectName.res via brcc32 (v$v, icon=$(if($iconFile){'yes'}else{'no'}))" -ForegroundColor Green
                    return $true
                } else {
                    Write-Warning "brcc32 failed: $brccOutput"
                }
            }
        }

        if (Test-Path $resFile) {
            Remove-Item $resFile -Force
        }

        if ($DprojFile -and (Test-Path $DprojFile) -and $RsVars -and (Test-Path $RsVars)) {
            try {
                $msbuildCmd = "call ""$RsVars"" && ""C:\Windows\Microsoft.NET\Framework\v4.0.30319\MSBuild.exe"" ""$DprojFile"" /t:BuildVersionResource /p:Config=$Config /p:Platform=Win32 /v:quiet"
                cmd /c $msbuildCmd 2>&1 | Out-Null
                if (Test-Path $resFile) {
                    Write-Host "[OK] Generated $projectName.res via MSBuild (version only, no icon)" -ForegroundColor Yellow
                    return $true
                }
            } catch {}
        }
    }

    if (Test-Path $resFile) { return $true }

    Write-Host "[INFO] $projectName.res not found, attempting to generate..." -ForegroundColor Yellow

    if ($DprojFile -and (Test-Path $DprojFile) -and $RsVars -and (Test-Path $RsVars)) {
        try {
            $msbuildCmd = "call ""$RsVars"" && ""C:\Windows\Microsoft.NET\Framework\v4.0.30319\MSBuild.exe"" ""$DprojFile"" /t:BuildVersionResource /p:Config=$Config /p:Platform=Win32 /v:quiet"
            cmd /c $msbuildCmd 2>&1 | Out-Null
            if (Test-Path $resFile) {
                Write-Host "[OK] Generated $projectName.res via MSBuild BuildVersionResource" -ForegroundColor Green
                return $true
            }
        } catch {}
    }

    if ($BRCC32 -and (Test-Path $BRCC32)) {
        try {
            $rcPath = Join-Path $env:TEMP "$projectName.rc"
            Set-Content $rcPath "" -Encoding ASCII
            & $BRCC32 -fo"$resFile" $rcPath 2>&1 | Out-Null
            Remove-Item $rcPath -Force -ErrorAction SilentlyContinue
            if (Test-Path $resFile) {
                Write-Host "[OK] Generated empty $projectName.res via brcc32" -ForegroundColor Green
                return $true
            }
        } catch {}
    }

    Write-Warning "$projectName.res could not be generated. Compilation may fail."
    return $false
}

function Find-MissingResFiles {
    param([string]$CompilerOutput)

    $missing = @()
    $pattern = "E1026 File not found: '(.+\.(?:res|RES))'"

    [regex]::Matches($CompilerOutput, $pattern) | ForEach-Object {
        $missing += $_.Groups[1].Value
    }

    return $missing | Select-Object -Unique
}

function Find-MissingUnit {
    param([string]$CompilerOutput)

    if ($CompilerOutput -match "F2613 Unit '([^']+)' not found") {
        return @{ Name = $Matches[1]; Type = "missing" }
    }
    return $null
}

function Find-FailedCompileUnit {
    param([string]$CompilerOutput)

    if ($CompilerOutput -match "F2063 Could not compile used unit '([^']+)\.pas'") {
        return $Matches[1]
    }
    return $null
}

function Resolve-FailedUnit {
    param(
        [string]$UnitName,
        [string[]]$CurrentPaths
    )

    foreach ($dir in $CurrentPaths) {
        if (-not (Test-Path $dir -ErrorAction SilentlyContinue)) { continue }

        $dcuFile = Join-Path $dir "$UnitName.dcu"
        $pasFile = Join-Path $dir "$UnitName.pas"

        if ((Test-Path $dcuFile) -and (Test-Path $pasFile)) {
            Write-Host "[FIX] Found $UnitName.dcu in source dir: $dir" -ForegroundColor Yellow
            Write-Host "[FIX] Copying DCUs from '$dir' to DCU output..." -ForegroundColor Yellow

            $dcuFiles = Get-ChildItem -Path $dir -Filter "*.dcu" -ErrorAction SilentlyContinue
            foreach ($f in $dcuFiles) {
                $dest = Join-Path $DCUOutputDir $f.Name
                Copy-Item $f.FullName $dest -Force
            }

            Write-Host "[FIX] Copied $($dcuFiles.Count) DCU files. Removing source dir from -U paths." -ForegroundColor Yellow
            return $dir
        }
    }

    return $null
}

function Create-EmptyRes {
    param([string]$ResName, [string]$TargetDir)

    if (-not $BRCC32 -or -not (Test-Path $BRCC32)) {
        Write-Warning "brcc32 not available, cannot create $ResName"
        return $false
    }

    $rcPath = Join-Path $env:TEMP "empty_placeholder.rc"
    $resPath = Join-Path $TargetDir $ResName

    Set-Content $rcPath "" -Encoding ASCII
    & $BRCC32 -fo"$resPath" $rcPath 2>&1 | Out-Null
    Remove-Item $rcPath -Force -ErrorAction SilentlyContinue

    if (Test-Path $resPath) {
        Write-Host "[OK] Created placeholder $ResName" -ForegroundColor Green
        return $true
    }

    Write-Warning "Failed to create $ResName"
    return $false
}

# --- Resolve output directories from .dproj ---
$dprojGroups = Get-DprojPropertyGroups

$userExeDir = $OutputDir
$userDcuDir = $DCUOutputDir
$userObjDir = $ObjOutputDir

Extract-DprojOutputPaths -Groups $dprojGroups

if ($userExeDir) { $OutputDir = $userExeDir }
if ($userDcuDir) { $DCUOutputDir = $userDcuDir }
if ($userObjDir) { $ObjOutputDir = $userObjDir }

if (-not $OutputDir) { $OutputDir = $ProjectDir }
if (-not $DCUOutputDir) { $DCUOutputDir = Join-Path $ProjectDir "dcu_$Config" }
if (-not $ObjOutputDir) { $ObjOutputDir = $DCUOutputDir }

foreach ($dir in @($OutputDir, $DCUOutputDir, $ObjOutputDir)) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

# --- Build search paths and compile ---
$searchPaths = Build-SearchPaths
$resourceOnlyPaths = @()

$workspaceRoot = Split-Path $ProjectDir -Parent
$bdsRoot = if ($BDS) { $BDS.TrimEnd('\', '/') } else { "" }
$bdsCommonRoot = if ($BDSCommonDir) { $BDSCommonDir.TrimEnd('\', '/') } else { "" }

$testRoot = $workspaceRoot
while ($testRoot) {
    $hasGit = Test-Path (Join-Path $testRoot ".git") -ErrorAction SilentlyContinue
    $hasDproj = (Get-ChildItem $testRoot -Filter "*.dproj" -ErrorAction SilentlyContinue | Select-Object -First 1) -ne $null
    if ($hasGit -or $hasDproj) {
        $workspaceRoot = $testRoot
        break
    }
    $parentTest = Split-Path $testRoot -Parent
    if ($parentTest -eq $testRoot) { break }
    $testRoot = $parentTest
}
$preFixPaths = @()
foreach ($sp in $searchPaths) {
    if (-not (Test-Path $sp -ErrorAction SilentlyContinue)) { continue }

    $isProjectPath = $sp.StartsWith($workspaceRoot, [StringComparison]::OrdinalIgnoreCase)
    if ($isProjectPath) { continue }

    $isBdsPath = ($bdsRoot -and $sp.StartsWith($bdsRoot, [StringComparison]::OrdinalIgnoreCase))
    $isBdsCommon = ($bdsCommonRoot -and $sp.StartsWith($bdsCommonRoot, [StringComparison]::OrdinalIgnoreCase))
    if ($isBdsPath -or $isBdsCommon) { continue }

    $hasDcu = (Get-ChildItem -Path $sp -Filter "*.dcu" -ErrorAction SilentlyContinue | Select-Object -First 1) -ne $null
    $hasPas = (Get-ChildItem -Path $sp -Filter "*.pas" -ErrorAction SilentlyContinue | Select-Object -First 1) -ne $null

    if ($hasDcu -and $hasPas) {
        $preFixPaths += $sp
    }
}

if ($preFixPaths.Count -gt 0) {
    Write-Host "[PRE-FIX] Found $($preFixPaths.Count) third-party source dirs with DCU+PAS. Copying DCUs proactively..." -ForegroundColor Yellow
    foreach ($pfp in $preFixPaths) {
        $dcuFiles = Get-ChildItem -Path $pfp -Filter "*.dcu" -ErrorAction SilentlyContinue
        foreach ($f in $dcuFiles) {
            $dest = Join-Path $DCUOutputDir $f.Name
            if (-not (Test-Path $dest)) {
                Copy-Item $f.FullName $dest -Force
            }
        }
        $searchPaths = $searchPaths | Where-Object { $_ -ne $pfp }
        $resourceOnlyPaths += $pfp
        Write-Host "  Copied $($dcuFiles.Count) DCUs from: $(Split-Path $pfp -Leaf)" -ForegroundColor DarkGray
    }
}

$cfgContent = Build-CfgContent -SearchPaths $searchPaths -ResourceOnlyPaths $resourceOnlyPaths

Write-Host "============================================" -ForegroundColor Cyan
Write-Host " Building: $projectName ($Config / Win32)" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "DPR:        $dprFullPath"
Write-Host "Output:     $OutputDir"
Write-Host "DCU:        $DCUOutputDir"
Write-Host "Paths:      $($searchPaths.Count) search paths"
Write-Host ""

Ensure-ResFile | Out-Null

[System.IO.File]::WriteAllText($cfgPath, $cfgContent, [System.Text.Encoding]::Default)

$maxAttempts = 6
$attempt = 0
$createdResFiles = @()
$excludedDirs = @()
$success = $false

while ($attempt -lt $maxAttempts -and -not $success) {
    $attempt++
    Write-Host "[Attempt $attempt/$maxAttempts] Compiling $DprFile..." -ForegroundColor White

    Push-Location $ProjectDir
    try {
        $output = & $DCC32 $DprFile 2>&1 | Out-String
        $exitCode = $LASTEXITCODE
    } finally {
        Pop-Location
    }

    Write-Host $output

    if ($exitCode -eq 0) {
        $success = $true
        Write-Host "[SUCCESS] $projectName compiled successfully!" -ForegroundColor Green
        break
    }

    $missingRes = Find-MissingResFiles -CompilerOutput $output
    $failedUnit = Find-FailedCompileUnit -CompilerOutput $output
    $missingUnit = Find-MissingUnit -CompilerOutput $output

    $handled = $false

    if ($missingRes.Count -gt 0) {
        Write-Host "[RETRY] Missing .res files detected, creating placeholders..." -ForegroundColor Yellow
        foreach ($res in $missingRes) {
            if (Create-EmptyRes -ResName $res -TargetDir $ProjectDir) {
                $createdResFiles += (Join-Path $ProjectDir $res)
            }
        }
        $handled = $true
    }

    if ($failedUnit) {
        $badDir = Resolve-FailedUnit -UnitName $failedUnit -CurrentPaths $searchPaths
        if ($badDir) {
            $excludedDirs += $badDir
            $resourceOnlyPaths += $badDir
            $searchPaths = $searchPaths | Where-Object { $_ -ne $badDir }
            $cfgContent = Build-CfgContent -SearchPaths $searchPaths -ResourceOnlyPaths $resourceOnlyPaths
            [System.IO.File]::WriteAllText($cfgPath, $cfgContent, [System.Text.Encoding]::Default)
            $handled = $true
        }
    }

    if ($missingUnit -and -not $handled) {
        $unitName = $missingUnit.Name
        Write-Host "[INFO] Missing unit: $unitName - searching workspace..." -ForegroundColor Yellow
        $workspaceRoot = Split-Path $ProjectDir -Parent
        $found = Get-ChildItem -Path $workspaceRoot -Filter "$unitName.pas" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($found) {
            $unitDir = Resolve-ShortPath -Path $found.DirectoryName
            Write-Host "[INFO] Found $unitName at: $unitDir" -ForegroundColor Green
            $searchPaths = @($unitDir) + $searchPaths | Select-Object -Unique
            $cfgContent = Build-CfgContent -SearchPaths $searchPaths -ResourceOnlyPaths $resourceOnlyPaths
            [System.IO.File]::WriteAllText($cfgPath, $cfgContent, [System.Text.Encoding]::Default)
            $handled = $true
        } else {
            Write-Error "[FAILED] Unit '$unitName' not found in workspace."
            break
        }
    }

    if (-not $handled) {
        Write-Error "[FAILED] $projectName compilation failed (exit code $exitCode)"
        break
    }
}

if (-not $KeepCfg) {
    Remove-Item $cfgPath -Force -ErrorAction SilentlyContinue
}

foreach ($tempRes in $createdResFiles) {
    Remove-Item $tempRes -Force -ErrorAction SilentlyContinue
    Write-Host "[CLEANUP] Removed placeholder: $(Split-Path $tempRes -Leaf)" -ForegroundColor DarkGray
}

$exePath = Join-Path $OutputDir "$projectName.exe"
if (Test-Path $exePath) {
    $exeInfo = Get-Item $exePath
    $sizeMB = [math]::Round($exeInfo.Length / 1MB, 1)

    Write-Host ""
    Write-Host "Output: $exePath ($sizeMB MB)" -ForegroundColor Green
    Write-Host "Time:   $($exeInfo.LastWriteTime)" -ForegroundColor Green
}

if ($success) { exit 0 } else { exit 1 }
