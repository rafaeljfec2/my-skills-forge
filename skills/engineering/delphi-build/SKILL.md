---
name: delphi-build
description: >-
  Detect Delphi/RAD Studio installation and compile .dpr/.dproj projects from
  the command line using dcc32 with .cfg files. Use when the user asks to
  compile, build, or make a Delphi project, or mentions dcc32, msbuild,
  RAD Studio, .dproj files, or Delphi compilation.
---

# Delphi Command-Line Build

Compiles Delphi projects using `dcc32.exe` with `.cfg` files, bypassing MSBuild's
command-line length limit. Handles third-party source conflicts, missing `.res`
files, and Unicode path issues.

## Workflow (thin orchestrator)

1. **Detect Delphi** — `powershell -ExecutionPolicy Bypass -File "<skill-dir>/scripts/detect-delphi.ps1"` (JSON with DCC32, paths). If detection fails, ask for the RAD Studio install path.
2. **Identify projects** — find `.dpr` files (git status, user input, or scan).
3. **Compile** — run `scripts/build-project.ps1` with DCC32, project dir, `.dpr`, Config, library paths, BRCC32, RsVars, `.dproj`, BDS paths.
4. **Compilar vs Buildar** — "compilar" = no `-RegenerateRes`; "buildar" = always add `-RegenerateRes` for version info.
5. **Report** — project name, success/failure, `.exe` path/size, time.
6. Script internals, cfg rationale, troubleshooting → [references/build-details.md](references/build-details.md)

Example install roots (not machine-specific): `C:\Program Files (x86)\Embarcadero\Studio`, `C:\Program Files\Embarcadero\Studio`.

## Token economy

Keep the injectable surface small. Read [references/build-details.md](references/build-details.md) only when debugging the build script behavior.
