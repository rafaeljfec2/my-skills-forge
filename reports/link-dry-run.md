# Relatório de link das skills do catálogo

Data: 2026-10-24  
Forge canônico: `C:\Users\rafae\dev-rafael\my-skills-forge` (`/mnt/c/Users/rafae/dev-rafael/my-skills-forge`)  
Atalho WSL: `/home/rafael/dev-rafael/my-skills-forge` → checkout acima  
Backup das pastas reais removidas: `~/skill-backup-2026-10-24/`

## Objetivo

O forge é a única cópia editável das **22** skills do catálogo. Harnesses e
projetos listados passam a apontar para o forge. Skills fora do catálogo,
skills de produto, `air-finance-sentinel`, Codex `.system` e `ai-memory-*`
permanecem onde estavam.

## O que foi feito

1. Backup + remoção de pastas reais do catálogo e nomes aposentados nos
   harnesses Cursor/Claude e nos projetos `connexto-vps-deploy-paas`,
   `connexto-stt-flow` e `connexto-job-search`.
2. Relocação do checkout para o disco Windows (junctions locais exigem
   caminho em `C:\`; `\\wsl$` e symlink privilegiado não estavam
   disponíveis nesta máquina).
3. `python3 scripts/link_skills.py` — Cursor com `mklink /J`; Claude,
   Codex e agents com symlink Linux.
4. Symlinks de projeto para nomes do catálogo:
   - `connexto-vps-deploy-paas/.cursor/skills/{business-rule-guardian,frontend-engineering-expert}`
   - `connexto-stt-flow/.{cursor,claude}/skills/gh-create-pr`
   - `connexto-job-search/.agents/skills/ui-implement-figma`

## Dry-run após o apply

```text
dry-run cursor: unchanged=22
dry-run claude: unchanged=22
dry-run codex: unchanged=22
dry-run agents: unchanged=22
```

Exit code: **0**. Zero `conflict-real` / `conflict-target`.

## O que continua local (fora do catálogo)

| Local | Pastas reais que permanecem |
|---|---|
| Cursor | `air-finance-sentinel`, `create-adr`, `create-rfc`, `create-technical-design-doc`, `gh-address-comments`, `gh-fix-ci`, `mermaid-studio`, `nestjs-modular-monolith` |
| Claude | `create-adr`, `create-rfc`, `create-technical-design-doc`, `gh-address-comments`, `gh-fix-ci`, `mermaid-studio`, `nestjs-modular-monolith` |
| Codex | `.system` |
| agents | `ai-memory-*` |
| Projetos de produto | skills de game-funny, banking-dev, axiom-*, frontend-dev, backend-dev, etc. |

## Próximo passo operacional

Reiniciar Cursor / Claude / Codex / agents para recarregar as descriptions
dos `SKILL.md`.
