---
name: mermaid-studio-compact
description: Expert Mermaid diagram creation, validation, and rendering with dual-engine output (SVG/PNG/ASCII). Supports all 20+ diagram types including C4 architecture, AWS architecture-beta with service icons, flowcharts, sequence, ERD, state, class, mindmap, timeline, git graph, sankey, and more. Features code-to-diagram analysis, batch rendering, 15+ themes, and syntax validation. Use when users ask to create diagrams, visualize architecture, render mermaid files, generate ASCII diagrams, document system flows, model databases, draw AWS infrastructure, analyze code structure, or anything involving "mermaid", "diagram", "flowchart", "architecture diagram", "sequence diagram", "ERD", "C4", "ASCII diagram". Do NOT use for non-Mermaid image generation, data plotting with chart libraries, or general documentation writing.
license: CC-BY-4.0
metadata:
  author: Felipe Rodrigues - github.com/felipfr
  version: 1.0.1
---

# Mermaid Studio

Expert-level Mermaid diagram creation, validation, and multi-format rendering. Creates diagrams from descriptions or code analysis, validates syntax, renders to SVG / PNG / ASCII with professional theming.

## Golden Rules — read FIRST

Every diagram MUST follow five non-negotiable rules (init directive, soft lines, density limits, meaningful labels, color harmony) plus full palette and quick examples for flowchart / C4 / architecture-beta.

Read `references/golden-rules.md` BEFORE writing any diagram.

## Modes of operation

| Mode       | Trigger                                           | What happens               |
| ---------- | ------------------------------------------------- | -------------------------- |
| **Create** | "draw a diagram of...", "visualize my..."         | Generates `.mmd` code only |
| **Render** | "render this mermaid", "convert to SVG/PNG/ASCII" | Renders existing `.mmd`    |
| **Full**   | "create and render...", ambiguous requests        | Create → Validate → Render |

Default to **Full** when intent is unclear.

## Step 1 — Understand the request

Before writing any Mermaid code, determine:

1. What to diagram — system, flow, schema, architecture, code structure?
2. Which diagram type — use the Decision Matrix below
3. Output format — code only, SVG, PNG, or ASCII?
4. Theme preference — ask only when rendering; default `base` with curated palette

### Diagram type decision matrix

| User describes...                              | Diagram Type  | Syntax keyword       |
| ---------------------------------------------- | ------------- | -------------------- |
| Process, algorithm, decision tree, workflow    | Flowchart     | `flowchart TD/LR`    |
| API calls, message passing, request/response   | Sequence      | `sequenceDiagram`    |
| Database schema, table relationships           | ERD           | `erDiagram`          |
| OOP classes, domain model, interfaces          | Class         | `classDiagram`       |
| State machine, lifecycle, transitions          | State         | `stateDiagram-v2`    |
| High-level system overview (C4 Level 1)        | C4 Context    | `C4Context`          |
| Applications, databases, services (C4 Level 2) | C4 Container  | `C4Container`        |
| Internal components (C4 Level 3)               | C4 Component  | `C4Component`        |
| Request flows with numbered steps              | C4 Dynamic    | `C4Dynamic`          |
| Infrastructure, cloud deployment               | C4 Deployment | `C4Deployment`       |
| Cloud services with icons (AWS/GCP/Azure)      | Architecture  | `architecture-beta`  |
| Project timeline, scheduling                   | Gantt         | `gantt`              |
| Proportional data, percentages                 | Pie           | `pie`                |
| Brainstorming, hierarchical ideas              | Mindmap       | `mindmap`            |
| Historical events, chronology                  | Timeline      | `timeline`           |
| Branching strategy, git history                | Git Graph     | `gitGraph`           |
| Flow quantities, resource distribution         | Sankey        | `sankey-beta`        |
| X/Y data visualization                         | XY Chart      | `xychart-beta`       |
| Priority matrix, strategic positioning         | Quadrant      | `quadrantChart`      |
| Layout control, grid positioning               | Block         | `block-beta`         |
| Network packets, protocol headers              | Packet        | `packet-beta`        |
| Task boards, kanban workflow                   | Kanban        | `kanban`             |
| User experience, satisfaction scoring          | User Journey  | `journey`            |
| System requirements traceability               | Requirement   | `requirementDiagram` |

If the user's description doesn't clearly map to one type, suggest 2-3 options with rationale and let them choose.

### When to load references

Load reference files only when needed:

- **Golden rules + palette + quick examples** → `references/golden-rules.md` (always before writing)
- **C4 diagrams** → `references/c4-architecture.md` BEFORE writing code
- **AWS/Cloud architecture** → `references/aws-architecture.md` BEFORE writing code
- **Code-to-diagram** → `references/code-to-diagram.md` BEFORE analyzing
- **Theming/styling** → `references/themes.md` for custom themes
- **Syntax errors** → `references/troubleshooting.md` when validation fails
- **Any diagram type details** → `references/diagram-types.md` for comprehensive syntax

## Step 2 — Create the diagram

Priority order:

1. **Elegance** — every diagram looks professional with init directives + curated colors
2. **Correctness** — valid syntax, renders without errors
3. **Clarity** — meaningful labels, logical flow direction, clear relationships
4. **Simplicity** — under 15 nodes; split complex systems into multiple diagrams
5. **Consistency** — uniform naming (camelCase IDs, descriptive labels in brackets)

### Structure

```
%% Diagram: [Purpose] | Author: [auto] | Date: [auto]
%%{init: {'theme': 'base', 'themeVariables': { ... }}}%%
[diagramType]
    [content]
```

The `%%{init}` directive MUST be the first non-comment line, BEFORE the diagram type. Alternatively, use YAML frontmatter at the absolute start.

### Layout

- `TD` (top-down) for hierarchical flows and processes
- `LR` (left-right) for timelines, pipelines, sequential processes
- `RL` for right-to-left reading contexts
- Use `subgraph` to group related nodes; name them meaningfully
- Add `direction` inside subgraphs when needed

## C4 diagrams — mandatory styling guide

C4 has fixed element styling but its relationship lines default to harsh black. You MUST apply soft styling.

Pattern:

```
    %% === MANDATORY STYLING ===
    UpdateRelStyle(fromAlias, toAlias, $textColor="#475569", $lineColor="#94a3b8")
    %% Repeat for each Rel() in the diagram

    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

CRITICAL: Maximum 6 `Rel()` per diagram. More than 6 causes Dagre to route arrows through nodes, creating unreadable spaghetti. Split into multiple focused diagrams.

Full C4 styling reference (color values, layout tips, full examples): `references/c4-architecture.md`.

## Step 3 — Validate

Before rendering, ALWAYS validate:

```bash
node $SKILL_DIR/scripts/validate.mjs <file.mmd>
```

If validation fails:

1. Read the error message carefully
2. Consult `references/troubleshooting.md`
3. Fix the syntax and re-validate
4. Maximum 3 fix attempts before asking the user

## Step 4 — Render

### Setup (first run only)

```bash
bash $SKILL_DIR/scripts/setup.sh
```

Auto-installs both rendering engines and icon pack dependencies.

### Single diagram

```bash
# SVG (default — best quality)
node $SKILL_DIR/scripts/render.mjs -i diagram.mmd -o diagram.svg

# PNG (for documents/presentations)
node $SKILL_DIR/scripts/render.mjs -i diagram.mmd -o diagram.png --width 1200

# ASCII (for terminals/READMEs)
node $SKILL_DIR/scripts/render-ascii.mjs -i diagram.mmd

# With icon packs (architecture-beta with AWS/tech icons)
node $SKILL_DIR/scripts/render.mjs -i diagram.mmd -o diagram.svg --icons logos,fa
```

The `--icons` flag registers Iconify packs before rendering. Packs: `logos` (AWS/tech), `fa` (Font Awesome). Use `logos` for AWS.

### Batch

```bash
node $SKILL_DIR/scripts/batch.mjs \
  --input-dir ./diagrams \
  --output-dir ./rendered \
  --format svg \
  --theme default \
  --workers 4
```

### Themes

15 beautiful-mermaid themes (`tokyo-night`, `dracula`, `nord`, `catppuccin-mocha`, `github-dark`, `solarized-dark`, `one-dark`, `zinc-dark`, etc.) and 5 mermaid-cli native (`default`, `forest`, `dark`, `neutral`, `base`).

Custom theme: `--theme base --config '{"theme":"base","themeVariables":{"primaryColor":"#4f46e5","lineColor":"#94a3b8"}}'`

Full theme catalog and engine selection rules: `references/themes.md`.

## Step 5 — Code-to-diagram (when requested)

When the user asks to visualize existing code or architecture:

1. Read `references/code-to-diagram.md` for the analysis methodology
2. Identify the right diagram type:
   - Module dependencies → Flowchart or Class
   - API routes and handlers → Sequence
   - Database models/schemas → ERD
   - Service architecture → C4 Container or Architecture
   - State machines → State diagram
3. Generate the `.mmd` file with proper init directives (Golden Rule 1)
4. Validate and render

## Troubleshooting quick reference

| Symptom               | Likely Cause       | Fix                                                    |
| --------------------- | ------------------ | ------------------------------------------------------ |
| Diagram won't render  | Syntax error       | Run `validate.mjs`, check brackets/quotes              |
| Labels cut off        | Text too long      | Shorten labels or use line breaks `<br/>`              |
| Layout looks wrong    | Wrong direction    | Try different `TD/LR/BT/RL`                            |
| Nodes overlap         | Too many nodes     | Split into subgraphs or multiple diagrams              |
| Lines too dark/thick  | No init directive  | Add `%%{init}` with `lineColor: '#94a3b8'`             |
| C4 lines overlapping  | No styling applied | Add `UpdateRelStyle` with offsets to each `Rel`        |
| AWS icons not showing | No icon pack       | Use `--icons logos` flag or fall back to built-in      |
| `mmdc` not found      | Not installed      | Run `setup.sh`                                         |
| Theme not applied     | Wrong engine       | beautiful-mermaid themes only work with that engine    |

Comprehensive troubleshooting: `references/troubleshooting.md`.

## Output conventions

- Save `.mmd` source files alongside rendered outputs
- Naming: `{purpose}-{type}.mmd` (e.g., `auth-flow-sequence.mmd`)
- For batch: maintain input filename, change extension
- Always provide both the `.mmd` source and rendered file to the user
