---
name: error-plan-then-fix
description: >-
  When the user shares error output (stack traces, ESLint/TS failures, Husky or
  lint-staged logs, CI logs, git-error excerpts, test failures, build errors),
  runs a short planning phase then implements fixes. Use when the user pastes
  errors, attaches failure logs, or asks to fix, debug, or resolve an error.
---

# Error: plan first, then fix

## When this skill applies

Read and follow this skill when the user message **includes or references** any of:

- Pasted terminal or editor output with `error`, `FAILED`, `✖`, stack traces
- Paths like `git-error-*`, `husky`, `lint-staged`, pre-commit failures
- CI/job logs, `eslint`, `tsc`, `vitest`, `jest`, build failures
- Explicit asks: “corrigir este erro”, “fix this”, “why did this fail”

If the user is in **Ask / read-only** mode, run **only** the planning phase and do not edit files or run mutating commands.

## Phase 1 — Modo planejador (obrigatório)

Before changing code or running fixes:

1. **Extrair sinais**: ferramenta (ESLint, Git, Turbo, etc.), ficheiros e linhas citados, código de saída.
2. **Hipóteses**: listar 2–4 causas plausíveis, ordenadas por probabilidade.
3. **Plano em fases**: passos concretos (ex.: confirmar ficheiro no disco vs stage → ajustar config → corrigir regra → validar com lint/teste).

Se faltar contexto crítico (repo errado, comando desconhecido, erro truncado), fazer **1–3 perguntas** objetivas e só depois fechar o plano.

Se a UI estiver em **Plan mode**, usar a ferramenta de plano do Cursor; caso contrário, apresentar o plano em markdown claro (título, causas, fases, ficheiros tocados).

**Não** saltar para implementação sem este bloco, exceto se o erro for trivial e o plano for uma única linha explícita (ex.: “typo óbvio na linha X”).

## Phase 2 — Resolver

After the plan (e após aprovação do plano, se o produto exigir confirmação explícita):

1. Investigar com ferramentas (ler ficheiros, grep, comandos de verificação).
2. Aplicar a **correção mínima** necessária; alinhar com convenções do repo.
3. Validar: lint/test/build adequado ao tipo de erro; não assumir sucesso sem correr o que fizer sentido.
4. Resumir em PT-BR: o que falhou, o que mudou, e como validar.

## Restrições

- Não editar `.env` com segredos sem autorização explícita do utilizador.
- Não executar comandos destrutivos ou `git push` sem confirmação quando as regras do utilizador o exigirem.
- Código e identificadores em inglês; resposta ao utilizador em **português (PT-BR)** salvo pedido em contrário.

## Anti-padrões

- Corrigir às cegas sem plano quando o log for longo ou ambíguo.
- Mudar comportamento de produto ou refatorar fora do âmbito do erro sem justificar.
- Ignorar que **Git stage** pode diferir do working tree (lint-staged falha no índice).
