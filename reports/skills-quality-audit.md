# Auditoria de qualidade das skills

Data: 2026-10-23 (homogeneização thin-orchestrator concluída)  
Coleção: `my-skills-forge` (20 skills em `skills/<domain>/<name>/`)  
Escopo: orçamento de contexto, contrato de forma, progressive disclosure e política de idioma.

## Método

### Orçamento de contexto

Mesma aproximação de [`skills/ai-agents/context-budget-guard`](../skills/ai-agents/context-budget-guard/SKILL.md):

- `tokens ≈ bytes / 3.5`
- `SKILL.md`: soft 2.500 / hard 4.000
- `references/*.md`: soft 5.000 / hard 7.000
- Preferência de forma: `SKILL.md` ≤ 1.500 tokens (aviso no `_validate.py`; orçamento soft 2.500 permanece)

Medido com `python3 skills/ai-agents/context-budget-guard/scripts/audit_budget.py --root .`.

### Contrato de forma

Documentado em [`references/skill-shape.md`](../references/skill-shape.md). Toda skill do catálogo deve ter:

- `## Workflow (thin orchestrator)`
- `## Token economy`

Validado por `_validate.py` (`check_skill_shape`).

### Lentes de curadoria (inspiradas no Akita)

Método de curadoria apenas — sem importar conteúdo do [akitaonrails/my-skills](https://github.com/akitaonrails/my-skills):

| Lente | Uso nesta auditoria |
|---|---|
| Economia de tokens: orquestrador fino | `SKILL.md` injetável; detalhe em `references/` |
| Forma útil mínima | Manter papéis distintos (reviews / PRs) |
| Inventário do que fica fora | README “Out of this repo / team-coupled” |
| Layout flat do Akita | **Não** adotado; pastas por domínio permanecem |

### Política de idioma

| Artefato | Idioma |
|---|---|
| Skills e docs do repositório | Inglês |
| Relatórios (`reports/**`) e planos | Português (PT-BR) |
| Chat com o maintainer | PT-BR |

## Resumo executivo

A coleção está **homogênea** no contrato thin-orchestrator: as 20 skills têm headings obrigatórios, progressive disclosure onde o corpo era monolítico, e orçamento OK.

| Métrica | Resultado |
|---|---|
| `SKILL.md` | **20 OK · 0 WARN · 0 FAIL** |
| `references/*.md` | **60 arquivos · todos OK** (agregado audit: OK=81 com regras alwaysApply) |
| Maior `SKILL.md` | `gh-create-pr` — 1.180 tok (soft 2.500) |
| Maior reference | `senior-code-review-judge/references/workflow-steps.md` — 4.750 tok (soft 5.000) |
| Preferência ≤1.500 tok | **20/20** skills do catálogo |

Quatro skills seguem `pending-review` no catálogo (licença/merge), não por orçamento: `pr-creator-tr`, `pr-creator-outcoders`, `senior-code-review-judge`, `senior-code-reviewer-protocol`.

## Tabela de orçamento (`SKILL.md`) — atual

| Domínio | Skill | Bytes | Tokens | Soft | Hard | Status |
|---|---|---|---|---|---|---|
| ai-agents | context-budget-guard | 1702 | 486 | 2.500 | 4.000 | OK |
| architecture | software-architecture-expert | 1822 | 520 | 2.500 | 4.000 | OK |
| design | ui-implement-figma | 2130 | 608 | 2.500 | 4.000 | OK |
| devops | gh-create-pr | 4133 | 1180 | 2.500 | 4.000 | OK |
| devops | pr-creator-outcoders | 1433 | 409 | 2.500 | 4.000 | OK |
| devops | pr-creator-tr | 1671 | 477 | 2.500 | 4.000 | OK |
| engineering | backend-engineering-expert | 1988 | 568 | 2.500 | 4.000 | OK |
| engineering | delphi-build | 1600 | 457 | 2.500 | 4.000 | OK |
| engineering | error-plan-then-fix | 1665 | 475 | 2.500 | 4.000 | OK |
| engineering | frontend-engineering-expert | 3156 | 901 | 2.500 | 4.000 | OK |
| engineering | performance-observability-expert | 1538 | 439 | 2.500 | 4.000 | OK |
| engineering | principal-engineering-workflow | 2146 | 613 | 2.500 | 4.000 | OK |
| engineering | sdd-workflow | 1597 | 456 | 2.500 | 4.000 | OK |
| productivity | job-search | 1423 | 406 | 2.500 | 4.000 | OK |
| quality | business-rule-guardian | 3408 | 973 | 2.500 | 4.000 | OK |
| quality | code-quality-standards | 2661 | 760 | 2.500 | 4.000 | OK |
| quality | qa-automation-expert | 1455 | 415 | 2.500 | 4.000 | OK |
| quality | senior-code-review-judge | 4081 | 1166 | 2.500 | 4.000 | OK |
| quality | senior-code-reviewer-protocol | 2770 | 791 | 2.500 | 4.000 | OK |
| security | application-security-expert | 1631 | 466 | 2.500 | 4.000 | OK |

### Referências

Todas sob soft 5.000. Observar `workflow-steps.md` do judge (~4.750) se crescer. Carga agregada ainda importa se o agente abrir todas as refs de uma vez; o orquestrador manda ler só o passo atual.

### Progressive disclosure

Suporte e fases longas vivem em `references/`. Scripts em `scripts/` não entram como texto de prompt.

## Homogeneização aplicada

1. Contrato em `references/skill-shape.md` + política de idioma no README e regras Cursor (forge + usuário).
2. P0: monolitos (`backend-engineering-expert`, `pr-creator-outcoders`, `ui-implement-figma`, `software-architecture-expert`) extraídos para `references/`.
3. P1: skills com refs alinhadas aos headings; `context-budget-guard`, PR creators, especialistas e `sdd-workflow` no formato orquestrador.
4. P2: skills pequenas com headings + Do NOT use onde há vizinhos.
5. P3: `_validate.py` exige headings; PROVENANCE com delta de homogeneização; este relatório em PT-BR.

## Clusters de papel (scoring tipo `reflect`)

### Reviews (quatro skills)

| Skill | Papel | Postura |
|---|---|---|
| principal-engineering-workflow | Autor fecha o próprio trabalho | Manter |
| senior-code-review-judge | Veredito evidence-first, sem fixes | Manter |
| senior-code-reviewer-protocol | Checklist Tech Lead / STFlow | Manter |
| business-rule-guardian | Gate de intenção em subagent readonly | Manter |

Não mesclar judge e protocol enquanto o perfil STFlow for o diferencial. Não dobrar guardian no judge: o subagent limpo é o produto.

### Pull requests (três skills)

| Skill | Público | Postura |
|---|---|---|
| gh-create-pr | Qualquer repo com template | Padrão portátil |
| pr-creator-tr | TR + ADO + Teams | Manter (acoplado) |
| pr-creator-outcoders | Outcoders + ADO | Manter (acoplado) |

## Achados abertos (baixo risco)

1. Licenças `pending-review` / `unknown` antes de publicação (checklist em LICENSING.md).
2. Vigiar `senior-code-review-judge/references/workflow-steps.md` perto do soft 5.000.
3. Apply real do linker pendente — ver [link-dry-run.md](link-dry-run.md) (12 `conflict-real` no Cursor).

## O que já está em boa forma

- Forma thin-orchestrator em 100% do catálogo.
- Orçamento soft/hard sem WARN/FAIL.
- Domínios alinhados aos papéis.
- Relatórios em PT-BR; skills/docs de governança em inglês.

## Apêndice — maturidade operacional (2026-10-24)

Leva Akita-like **sem** remodelar SKILL.md de novo:

| Entrega | Status |
|---|---|
| Inventário externo | [references/external-inventory.md](../references/external-inventory.md) |
| Dry-run do linker | [link-dry-run.md](link-dry-run.md) — apply real **não** executado |
| Skill `reflect` | `skills/ai-agents/reflect/` no catálogo |
| Fronteira publish/licença | [publish-boundary.md](../references/publish-boundary.md) + checklist em LICENSING.md |
| Higiene de secrets | `.gitignore` + scan em `_validate.py` (skills + governança) |

## Verificação

- Skills no catálogo: **22** (inclui `reflect` e `snyk-rules`)
- Orçamento atual: SKILL/refs OK (`audit_budget.py --root .` → Summary OK=85 WARN=0 FAIL=0)
- `_validate.py`: ALL VALIDATIONS PASSED (`check_skill_shape` + `check_governance_secrets`)
- `test_audit_budget.py`: 18 testes OK
- `link_skills.py --check-repo`: OK; `--dry-run`: exit 1 por conflitos Cursor (esperado)
- Princípios Akita usados só como método de curadoria; nenhum conteúdo Akita importado
