# Relatório dry-run do linker

Data: 2026-10-24  
Comandos: `python3 scripts/link_skills.py --check-repo` e `python3 scripts/link_skills.py --dry-run`  
Forge: `/home/rafael/dev-rafael/my-skills-forge`  
Escopo: **somente preview** — nenhum symlink foi criado nesta entrega.

## check-repo

```text
OK install map (22 skills)
```

Catálogo atual: 22 skills (inclui `reflect` e `snyk-rules`).

## Resumo por harness

| Harness | Diretório | create | conflict-real | Observação |
|---|---|---|---|---|
| cursor | `~/.cursor/skills` → `/mnt/c/Users/rafae/.cursor/skills` | 10 | 12 | Dirs reais bloqueiam link |
| claude | `~/.claude/skills` | 22 | 0 | Nomes do catálogo livres; há dirs legados com outros nomes |
| codex | `~/.codex/skills` | 22 | 0 | `.system` permanece (protegido) |
| agents | `~/.agents/skills` | 22 | 0 | `ai-memory-*` não colide com nomes do forge |

Exit code do dry-run: **1** (esperado enquanto houver `conflict-real` no Cursor).

Saída capturada:

```text
dry-run cursor: conflict-real=12 create=10
  conflict-real application-security-expert
  conflict-real backend-engineering-expert
  conflict-real code-quality-standards
  conflict-real delphi-build
  conflict-real error-plan-then-fix
  conflict-real frontend-engineering-expert
  conflict-real performance-observability-expert
  conflict-real principal-engineering-workflow
  conflict-real qa-automation-expert
  conflict-real snyk-rules
  conflict-real software-architecture-expert
  conflict-real ui-implement-figma
dry-run claude: create=22
dry-run codex: create=22
dry-run agents: create=22
Link incomplete. Real directories were left in place.
```

## Conflitos Cursor (`conflict-real`)

O linker **não** substitui diretório real. Estes nomes já existem como pasta no harness Cursor:

1. `application-security-expert`
2. `backend-engineering-expert`
3. `code-quality-standards`
4. `delphi-build`
5. `error-plan-then-fix`
6. `frontend-engineering-expert`
7. `performance-observability-expert`
8. `principal-engineering-workflow`
9. `qa-automation-expert`
10. `snyk-rules`
11. `software-architecture-expert`
12. `ui-implement-figma`

Para o forge vencer: backup → remover/renomear o dir real → `python3 scripts/link_skills.py` (sem `--dry-run`).

Também no Cursor e **fora** do fluxo create (protegidos / aposentados):

- `air-finance-sentinel` (protegido — nunca substituir)
- Nomes aposentados: `buscar-vagas-ti`, `pr-creator-ado`, `senior-code-reviewer`, `cognitive-complexity-guard`, etc. (ver [install-map](../references/install-map.md) e [external-inventory](../references/external-inventory.md))

## Claude / Codex / agents

Para os **22** nomes do catálogo: ação prevista `create`.

- Claude ainda tem pastas reais com nomes **não** listados no catálogo (`create-adr`, `mermaid-studio`, …) — o linker não as apaga.
- Codex mantém `.system`.
- agents mantém `ai-memory-*`.

## Próximos passos (manual)

1. Revisar a lista `conflict-real` acima.
2. Backup/remoção por skill no Cursor quando for para o forge vencer.
3. `python3 scripts/link_skills.py` (apply real).
4. Reiniciar Cursor / Claude / Codex / agents.
5. Reexecutar `--dry-run` e esperar `unchanged` / zero conflict.

## Segurança

Não copiar `air-finance-sentinel` para o forge. Não commitar `.env` / keys / tokens.
