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
