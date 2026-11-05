# Entrega — Connexto Development Workflow

Data: 2026-11-05  
Repositório: `my-skills-forge`  
Estado: skill local `pending-review`. Merge, publicação e deploy não foram feitos.

## Diagnóstico

O forge já era o catálogo de skills (`skills/<domínio>/<nome>/SKILL.md`), com linker e validador. Foram reutilizados, sem segunda cópia do texto:

| Recurso | Uso |
|---|---|
| `sdd-workflow` | Lei de fases. O passo 3 da fase 7 continua exigindo `senior-code-review-judge`. |
| `principal-engineering-workflow` | Higiene do autor dentro de IMPLEMENT. |
| `iterative-sdd-workflow` | Correção única com aceite humano. Não é o ciclo autônomo. |
| `senior-code-review-judge` | Veredito independente quando a entrega segue SDD. |
| `references/skill-shape.md` | Orquestrador fino, referências e orçamento de tokens. |
| Python já usado em `scripts/` | Runtime do MVP, biblioteca padrão, sem dependência nova. |

Não havia estado recuperável, adaptador de comandos do projeto nem log de evidência. Isso foi criado. A consulta ao AI Memory está em [connexto-workflow-memory-consultation.md](connexto-workflow-memory-consultation.md).

## Arquitetura

A skill `skills/engineering/connexto-development-workflow` é a camada de execução. O alvo não copia o framework: adiciona `connexto.project.json` e ignora `.connexto/`.

O checkpoint é `<alvo>/.connexto/runs/<id>/state.json`. Cada transição grava `evidence/execution.jsonl`. Cada comando grava argv, código de saída e trechos redatados em `evidence/commands.jsonl`.

Papéis no mesmo processo, com permissão separada por papel e id de ator: orchestrator, researcher, planner, developer, reviewer. O id de ator não é um usuário do sistema operacional.

Estados: `PENDING → INTAKE → RESEARCH → PLAN → IMPLEMENT → VALIDATE → REVIEW → DELIVERY → MEMORY → DONE`, mais `WAITING_APPROVAL`, `BLOCKED`, `FAILED` e `CANCELLED`. Arestas que pulam comando, review ou memória são recusadas no `transition`.

## Implementação

- Máquina de estados, schema JSON, gates de risco, aprovação, tentativas, commit e memória: `scripts/connexto_workflow/`.
- CLI: `scripts/cdw.py`.
- Contratos operacionais: `references/lifecycle.md`, `roles.md`, `policies.md`, `artifacts.md`, `memory.md`, `project-adapter.md`.
- Modelos em `templates/`.
- O schema é JSON de propósito. Não há PyYAML no ambiente, e o MVP não ganha dependência para ler o exemplo em YAML.

Risco padrão: BUGFIX e TECHNICAL_DEBT = LOW; FEATURE e REFACTOR = MEDIUM; HOTFIX = HIGH. Dá para subir o risco. Não dá para baixar. HIGH espera `start_high_risk` aprovado por outro ator. Ação protegida também espera outro ator e, neste MVP, não é executada.

## Validação

Testes do mecanismo, no diretório `scripts/` da skill:

```bash
python3 -m unittest discover -s tests -q
```

Resultado: 26 testes, OK, cerca de 1,8 s, Python 3.8. Cobrem schema, transição inválida, retorno de pesquisa e plano, limite de tentativas, retomada, isolamento de runs, snapshot de config, risco, aprovação, review do mesmo ator, severidade por risco, segredo em commit, bloqueio, timeout, redaction e o fluxo completo.

Prova ponta a ponta, repositório git temporário, sem rede e sem LLM:

```bash
python3 skills/engineering/connexto-development-workflow/scripts/cdw.py proof \
  --dest /tmp/connexto-workflow-mvp-20261105
```

| Campo | Valor observado |
|---|---|
| Demanda | `FEAT-001` |
| Estado final | `DONE` |
| Estado após novo `load()` | `DONE` |
| Teste | exit 1 (`ModuleNotFoundError: calc`), depois exit 0 |
| Hook `apply_fix.py` | exit 0 |
| Branch | `connexto/FEAT-001` |
| Commit | `5f0d8bf9fcdda465452ddcef00a5f10d60dcbb6b` |
| Reviewer | `rev-1`, diferente de `dev-1`, 0 achados |
| Release | merge, production_publish e deploy = `not performed` |

O primeiro teste falhou de verdade porque `calc.py` não existia. O hook escreveu a função. O segundo teste passou. O commit está só na branch de trabalho desse diretório temporário, não neste forge.

Checagens do forge no mesmo dia: catálogo e proveniência OK; estrutura OK (24 skills); varredura de segredo OK. A falha de formato de skill continua só em `skills/security/snyk-rules/SKILL.md`, anterior a esta mudança. Snyk Code devolveu 403 `SNYK-CODE-0005` (Snyk Code desligado na organização). Não foi ligado nesta sessão.

Orçamento da skill nova: `SKILL.md` ~724 tokens. A maior referência, `lifecycle.md`, ~1191. Abaixo dos tetos do forge.

## AI Memory

- Consulta: projeto `default` / `rafaeljfec2-my-skills-forge`.
- Página desta decisão: `decisions/connexto-development-workflow.md`.
- A prova grava `memory_ack_page = runs/FEAT-001.md` só no checkpoint temporário. Esse caminho não foi enviado ao servidor pelo processo da prova. O CLI não chama o servidor. O ack é o registro do caminho que o orquestrador afirma ter gravado.

## Adoção em outro repositório

Passos em inglês, no adaptador:

`skills/engineering/connexto-development-workflow/references/project-adapter.md`

Resumo: criar `connexto.project.json` só com comandos que já existem, ignorar `.connexto/`, invocar a skill pelo link do forge e dirigir `cdw.py --repo` para esse repositório. Não copiar a skill para dentro do produto.

## Pendências

- Codificação autônoma sem hook: o desenvolvedor continua sendo um agente, ou um comando declarado.
- O id do revisor não é uma identidade autenticada.
- O CLI não grava no AI Memory sozinho.
- Não há merge, deploy nem alteração de infraestrutura.
- Snyk Code não está habilitado.
- `snyk-rules` segue fora do formato fino. Fora do escopo desta entrega.
- A skill está `pending-review` por licença `unknown`, no mesmo critério de `iterative-sdd-workflow`.
- O linker dos harnesses não foi executado. A skill passa a ser instalada na próxima rodada de `scripts/link_skills.py`.

## Próximo incremento

Uma demanda pequena num repositório de produto, com `commands.implement` nulo, edição feita pelo agente, `memory-ack` só depois que o servidor aceitar a página, e o juiz em subagente somente leitura quando a entrega for SDD.
