# Connexto Development Workflow — Hardening v0.2

**Data:** 2026-11-05  
**Escopo:** MY-SKILLS-FORGE (`skills/engineering/connexto-development-workflow`)

## Resumo executivo

A v0.2 corrige os três gaps P0 da avaliação 7,2/10 (autonomia 6,5/10): **Developer com contrato e backend configurável**, **Reviewer via `senior-code-review-judge` em processo/sessão separados**, e **AI Memory com ciclo preparado → enviado → confirmado** (sem confundir ack local com persistência remota). A fundação v0.1 (state machine, gates, isolamento, 26 testes) foi preservada.

## A. Implementado e validado localmente

| Área | O que mudou | Evidência |
|------|-------------|-----------|
| Developer | `developer/task.json`, `submit_developer_report`, `run_developer_backend`; `commands.implement` null não bloqueia — exige relatório estruturado | 26 testes + 5 testes v0.2; `cdw develop-task`, `run-developer`, `develop-report` |
| Reviewer | `review/judge-input/bundle.json`, `run_independent_judge`, sessões distintas (`developer_session_id` / `reviewer_session_id`), limite `max_review_rounds` | `test_v02.py`; proof com `judge_worker.py` |
| AI Memory | `memory-sync`, estados `memory_remote_status`, workers de referência read/write | `test_v02.py` (round-trip local store) |
| Config | Seção `workflow` em `connexto.project.json` | template + `parse_config` |
| Proof | Sem hook `apply_fix.py`; backends subprocess | `python3 cdw.py proof --dest /tmp/connexto-v02-proof` → DONE, sessões distintas |

**Comandos executados:**

```bash
python3 scripts/tests/test_workflow.py   # 26 OK
python3 scripts/tests/test_v02.py        # 5 OK
python3 .../cdw.py proof --dest /tmp/connexto-v02-proof
python3 scripts/link_skills.py --check-repo
```

## B. Integrado e confirmado remotamente

- **AI Memory (servidor):** páginas gravadas nesta sessão em `default/rafaeljfec2-my-skills-forge` (ver `notes/connexto-workflow-hardening-v0.2-*.md` e read-back na entrega).
- **Linker:** `--check-repo` OK (24 skills no mapa). `--dry-run` não altera harnesses; adoção em outro repo continua documentada em `references/project-adapter.md` + execução manual de `link_skills.py` no ambiente do operador.

## C. Validado em execução real de produto

**Pendente.** Não foi executada prova em repositório de produto distinto do demo/proof temporário nesta sessão. Condições recomendadas: demanda pequena, `commands.implement` null, `workflow.developer_command` apontando para runtime de agente real (Cursor/CLI), `judge_command` invocando subagente readonly `senior-code-review-judge`, `memory_write_command`/`memory_read_command` ligados ao MCP/CLI ai-memory do operador.

## D. Pendências operacionais

1. Prova operacional em repo de produto (item C).
2. `_validate.py` do forge: falha pré-existente em `snyk-rules` headings (fora do escopo).
3. Skill ainda `pending-review` no CATALOG até revisão humana do forge.
4. Backends em `scripts/backends/*` são **referência** para testes/proof — produção deve substituir por invocação real de agente sem embutir lógica de solução no hook.

## Preservado (v0.1)

State machine, `state.json`, gates de aprovação/risco, reviewer ≠ developer actor, tentativas de validate, redaction, commit em branch isolada, delivery sem claim de merge/deploy, `evidence/commands.jsonl`.

## Avaliação honesta (pós v0.2)

| Dimensão | Antes | Depois (estrutural) | Autonomia comprovada |
|----------|-------|---------------------|----------------------|
| Workflow MVP | 7,2 | ~8,0 (contratos + testes) | proof subprocess, não LLM real |
| Autonomia efetiva | 6,5 | mecanismos prontos | **6,8–7,0** até prova C |

A nota de autonomia **não** sobe para 8+ enquanto Developer/Judge forem workers de referência ou agente real não rodar em repo de produto com memory remoto confirmado.

## Arquivos principais alterados

- `scripts/connexto_workflow/{engine,config,state,developer,reviewer,memory_sync,review_schema,backends,proof,cli,model,workflow_defaults}.py`
- `scripts/backends/{dev_worker,judge_worker,memory_write_worker,memory_read_worker}.py`
- `scripts/tests/{support,test_workflow,test_v02}.py`
- `templates/connexto.project.json`
