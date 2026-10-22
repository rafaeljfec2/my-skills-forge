---
name: delphi-build
description: >-
  Detect Delphi/RAD Studio installation and compile .dpr/.dproj projects from
  the command line using dcc32 with .cfg files. Use when the user asks to
  compile, build, or make a Delphi project, or mentions dcc32, msbuild,
  RAD Studio, .dproj files, or Delphi compilation.
---

# Delphi Command-Line Build

Compiles Delphi projects using `dcc32.exe` directly with `.cfg` files, bypassing MSBuild's 32000-char command-line limit. Handles third-party component source conflicts, missing .res files, and Unicode path issues automatically.

## Quick Start

### Step 1 -- Detect Delphi

```powershell
powershell -ExecutionPolicy Bypass -File "<skill-dir>/scripts/detect-delphi.ps1"
```

Returns JSON with `DCC32`, `BRCC32`, `RsVars`, `LibrarySearchPath`, `BDSCommonDir`, `RootDir`, etc. If detection fails, ask the user for the RAD Studio install path.

### Step 2 -- Identify Projects

Find `.dpr` files to compile. Use git status, user input, or workspace scan.

### Step 3 -- Compile Each Project

```powershell
powershell -ExecutionPolicy Bypass -File "<skill-dir>/scripts/build-project.ps1" `
  -DCC32 "<dcc32>" `
  -ProjectDir "<dir-containing-dpr>" `
  -DprFile "<project>.dpr" `
  -Config "Debug" `
  -LibrarySearchPath "<from-detect-output>" `
  -BRCC32 "<brcc32>" `
  -RsVars "<rsvars.bat>" `
  -DprojFile "<project>.dproj" `
  -BDS "<root-dir>" `
  -BDSCommonDir "<bds-common-dir>"
```

Optional: `-ExtraSearchPaths "<additional;semicolon;paths>"`, `-OutputDir`, `-DCUOutputDir`, `-KeepCfg`, `-RegenerateRes`

### Compilar vs Buildar

There are two workflows:

- **Compilar** (compile): Just compiles without touching version info. Uses existing `.res` file. Fast for dev iterations. Run the command above as-is.
- **Buildar** (build): Regenerates the `.res` file from the `.dproj` to embed updated version info into the executable. Add the `-RegenerateRes` switch:

```powershell
# Same command as Step 3, but adding -RegenerateRes at the end
... -RegenerateRes
```

When the user asks to "compilar", do NOT add `-RegenerateRes`.
When the user asks to "buildar", ALWAYS add `-RegenerateRes` so version info is refreshed.

### Step 4 -- Report Results

Summarize: project name, success/failure, .exe path and size, time.

## What the Build Script Does Automatically

1. **Reads output directories from `.dproj`**: parses `DCC_ExeOutput`, `DCC_DcuOutput`, `DCC_ObjOutput` respecting the Delphi config hierarchy (`Base` → `Base_Win32` → `Cfg_1`/`Cfg_2` → `Cfg_1_Win32`/`Cfg_2_Win32`). Falls back to project dir if not configured.
2. **Extracts search paths** from `.dproj` XML (`DCC_UnitSearchPath`) and merges with registry paths
3. **Pre-fixes third-party source conflicts**: scans search paths for directories containing both `.dcu` and `.pas` files outside the workspace. Copies DCUs to the output directory and removes those dirs from `-U` (keeping them in `-R`/`-I` for DFM/include resolution)
4. **Generates `.res` files** if missing (via MSBuild `BuildVersionResource` or `brcc32`)
5. **Creates empty placeholder .res** for missing third-party resources (e.g., `libeay32.RES`)
6. **Resolves Unicode paths** using 8.3 short names
7. **Searches workspace** for missing units and adds their directory
8. **Retries** up to 6 times with progressive self-healing

## Key Technical Details

### Why not MSBuild directly?

Projects with many third-party components on long OneDrive paths exceed Windows' 32767-char CreateProcess limit. The `.cfg` file bypasses this entirely.

### Config differences

| Setting | Debug | Release |
|---------|-------|---------|
| Optimization `-$O` | Off | On |
| Stack frames `-$W` | On | Off |
| Debug info `-$D` | On | Off |
| Defines `-D` | `DEBUG` | `RELEASE` |
| Symbols `-V`/`-VN` | Included | Omitted |

### Compile order

When compiling multiple related projects, compile smaller/simpler ones first (e.g., services before the main app).

## Troubleshooting

| Error | Cause | Auto-fix |
|-------|-------|----------|
| `F2063 Could not compile used unit` | Third-party source recompilation | Copies DCUs, removes source from -U |
| `E1026 File not found: '*.res'` | Missing resource file | Creates empty .res via brcc32 |
| `E1026 File not found: '*.RES'` | Missing third-party .res | Creates placeholder, deletes after |
| `F2613 Unit not found` | Missing unit path | Searches workspace, adds path |
| Unicode path failures | Non-ASCII in search paths | Uses 8.3 short names |

## Script Reference

- [detect-delphi.ps1](scripts/detect-delphi.ps1): Finds Delphi via registry + filesystem fallback
- [build-project.ps1](scripts/build-project.ps1): Generates .cfg, compiles, self-heals errors


## Example install roots

Detection scripts probe common Embarcadero install locations such as
`C:\Program Files (x86)\Embarcadero\Studio` and
`C:\Program Files\Embarcadero\Studio`. Treat these as examples of
standard install roots, not as a fixed path on a specific machine.
If detection fails, ask the user for the RAD Studio install path.
