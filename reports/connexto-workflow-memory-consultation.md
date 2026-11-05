# Consulta ao AI Memory — Connexto Development Workflow

Data: 2026-11-05  
Projeto consultado: `default` / `rafaeljfec2-my-skills-forge`  
Resolução: `shared_slot` (cliente com sessão; não havia `.ai-memory.toml` no repositório)  
Ferramentas: `memory_status`, `memory_briefing` (`settled_first: true`), `memory_recent`, `memory_query` (projeto e `global: true`), `memory_read_page`, `memory_read_session_observations`

## Briefing

| Campo | Valor |
|---|---|
| Páginas atuais | 5 (13 versões) |
| Sessões | 39 |
| Observações | 3809 |
| Linhas de evidência | 0 |
| Atividade 7 dias | 7 sessões, 771 observações, 5 páginas |
| Handoffs pendentes | 2 (um handoff de 2026-11-03 já veio no contexto desta sessão) |
| Páginas em `_rules/` | nenhuma |
| Última observação | 2026-11-05T12:38:36Z |

## Termos pesquisados

- Arquitetura, organização de skills, convenções de agentes e layout do forge
- RPI, SDD, TDD, Spec Kit, revisão e quality gates
- Automação, orquestração, evidência, AI Memory, máquina de estados
- Connexto Development Workflow, decisões rejeitadas e pendentes
- Busca global: `connexto development workflow`, `my-skills-forge` migration plan

## Decisões relevantes

Aceitas e ainda válidas no repositório (confirmadas no código, não só na memória):

- O forge é a fonte única editável das skills. Harnesses apontam para cá. Sessão `241faccc-3b2e-4afc-a383-dc23b5a6f930`.
- Skills de catálogo seguem o orquestrador fino: `references/skill-shape.md`.
- Relatórios e planos de entrega ficam em português; skills e documentação do repositório ficam em inglês. Regra de idioma do forge e pedido na mesma sessão.
- `sdd-workflow` é a lei de fases. Nenhuma fase pode ser pulada. O passo 3 da fase 7 precisa de um subagente só de leitura com `senior-code-review-judge`. Handoff de 2026-11-03 e sessão `828c2e1b-d315-4ce8-8577-724b15a631d9` (pedido de 2026-11-03: o agente estava pulando o review).
- `principal-engineering-workflow` é higiene do autor. Não substitui o review independente.
- `iterative-sdd-workflow` é manual, uma correção por vez, com aceite humano. Não é o ciclo autônomo.
- Perfil global `profile/habits/the-goal-is-to-prepare-a-migration-plan-for-my-new-repositor.md`: skills reutilizáveis e agnósticas de tecnologia.

Fora de escopo, embora esteja “settled”:

- `decisions/cursor-sdk-getusage-ai-hub-discovery.md` trata de uso faturado do Cursor SDK no AI Hub. Não define arquitetura deste forge.

Não encontrado:

- Página que aceite, rejeite ou desenhe um “Connexto Development Workflow”.
- Spec Kit como artefato deste repositório.
- `_rules/` ou linhas de evidência (`evidence_rows: 0`) sobre orquestração.

## Abordagens já rejeitadas

- Copiar skills de terceiros que não são do mantenedor. Na sessão `241faccc`, o pedido foi apagar skills e referências de AI Memory que não eram dele, e também skills do catálogo Tech Leads Club.
- Fundir `senior-code-review-judge` com `senior-code-reviewer-protocol`. O catálogo marca a fusão como fora de escopo.
- Tratar o self-review do autor como se fosse o juiz da fase 7.

## Limitações de acesso

- As páginas de sessão são resumos heurísticos (M3, sem LLM). O miolo das observações foi omitido. A leitura filtrada de prompts devolveu títulos, não o texto integral das decisões de arquitetura.
- Não há evidência estruturada anterior (`evidence_rows: 0`). O que vale como decisão é o que o código e o catálogo ainda mostram.
- A busca global não achou este workflow em outro projeto. Hits com “Connexto” são de produtos (AI Hub, proxy, signer, FlowDeploy), não deste desenho.
- Memória histórica não foi tratada como instrução operacional.

## Consequência para o desenho

Reutilizar `sdd-workflow`, `principal-engineering-workflow`, `iterative-sdd-workflow`, `senior-code-review-judge`, `qa-automation-expert` e `application-security-expert`. Criar somente o runtime que ainda não existe: estado recuperável, adaptador de projeto, gates e evidência. Não recolocar skills de AI Memory de terceiros no catálogo; a integração fica como contrato de payload e confirmação de página.
