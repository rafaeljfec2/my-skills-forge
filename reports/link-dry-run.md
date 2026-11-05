# Relatório de link das skills do catálogo

Data: 2026-10-24  
Atualizado em: 2026-10-28 (harness OpenCode adicionado)  
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

## 2026-10-28 — harness OpenCode adicionado

O OpenCode já descobria as 22 skills por compatibilidade
(`~/.claude/skills` e `~/.agents/skills`), porém sem fonte nativa. Passou a ser
consumidor explícito do linker:

```python
Harness("opencode", home / ".config" / "opencode" / "skills"),
```

- `~/.config/opencode/skills` criado — o linker exige que o diretório do
  harness já exista, comportamento igual aos demais consumidores.
- 22 symlinks Linux criados apontando para `skills/<domain>/<name>` no forge.
- Zero links quebrados (`find -xtype l` → 0).
- Dry-run pós-apply:

```text
dry-run cursor: unchanged=22
dry-run claude: unchanged=22
dry-run codex: unchanged=22
dry-run agents: unchanged=22
dry-run opencode: unchanged=22
```

Precedência no OpenCode: built-in → `.claude/skills` → `.agents/skills` →
`~/.config/opencode/skills` → projeto `.opencode/skills` → `skills` do config.
ID repetido entre fontes não é erro: a fonte de maior precedência vence.

## O que continua local (fora do catálogo)

| Local | Pastas reais que permanecem |
|---|---|
| Cursor | `air-finance-sentinel`, `create-adr`, `create-rfc`, `create-technical-design-doc`, `gh-address-comments`, `gh-fix-ci`, `mermaid-studio`, `nestjs-modular-monolith` |
| Claude | `create-adr`, `create-rfc`, `create-technical-design-doc`, `gh-address-comments`, `gh-fix-ci`, `mermaid-studio`, `nestjs-modular-monolith` |
| Codex | `.system` |
| agents | `ai-memory-*` |
| OpenCode | nenhuma — todas as skills do catálogo são links para o forge |
| Antigravity | `ui-implement-figma` (real); `ai-memory-*` |
| Antigravity CLI | `ai-memory-*` |
| Projetos de produto | skills de game-funny, banking-dev, axiom-*, frontend-dev, backend-dev, etc. |

## 2026-11-04 — harness Antigravity adicionado

Antigravity / Gemini passou a ser consumidor do linker:

```python
Harness("antigravity", home / ".gemini" / "config" / "skills"),
Harness("antigravity-cli", home / ".gemini" / "antigravity-cli" / "skills"),
```

- Destino global (docs Antigravity): `~/.gemini/config/skills`
- Destino CLI: `~/.gemini/antigravity-cli/skills`
- **Builtin** (`antigravity/builtin/skills`, `antigravity-ide/builtin/skills`) permanece package-owned — o linker não escreve lá

Apply (`python3 scripts/link_skills.py`, 2026-11-04):

```text
antigravity: conflict-real=1 create=22   → pós-apply: conflict-real=1 unchanged=22
  conflict-real ui-implement-figma
antigravity-cli: create=23               → pós-apply: unchanged=23
```

`ui-implement-figma` em `~/.gemini/config/skills` é pasta real (cópia antiga);
o linker não a substitui até backup/remoção manual. Demais 22 nomes no
Antigravity e todas as 23 no Antigravity CLI já apontam para o forge.

## Próximo passo operacional

Reiniciar Cursor / Claude / Codex / agents / OpenCode / Antigravity para
recarregar as descriptions dos `SKILL.md`. Opcional: backup + remover
`~/.gemini/config/skills/ui-implement-figma` e re-rodar o linker para
eliminar o último `conflict-real`.
