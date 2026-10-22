---
name: principal-engineering-workflow
description: >-
  Default engineering workflow for delivery-quality work. After every implementation
  (feature, bugfix, refactor), requires a meticulous self code review, concrete
  correction proposals, applying fixes, and validating with lint/tests/build before
  closing the task. Use whenever implementing code, shipping changes, or when the user
  expects a complete delivery—not only when they explicitly ask for review.
---

# Principal engineering workflow

This skill defines the **mandatory closure** after any implementation. Treat it as the default bar for “trabalho concluído”.

## Quando aplicar

- Sempre que tiveres **alterado código** (ficheiros criados, editados ou removidos) em resposta a um pedido.
- Antes de declarar a tarefa **feita** ou pedires merge/PR ao utilizador.

## Fluxo obrigatório (pós-implementação)

### 1. Code review minucioso das próprias alterações

Rever como Tech Lead o que foi entregue:

- **Arquitetura e limites**: coesão, acoplamento, impacto em outros módulos.
- **Correção e edge cases**: null/undefined, erros assíncronos, abort/cancel, i18n se aplicável.
- **Segurança**: inputs, segredos, injeção, exposição de dados, OWASP relevante ao stack.
- **Performance e observabilidade**: N+1, payloads, logs úteis sem dados sensíveis.
- **Padrões do projeto**: regras do utilizador (ex.: `??` vs `||`, sem `any`, mobile first no frontend, props `readonly`, `Promise.all` só onde faz sentido).
- **Testes**: cobertura do que mudou; descrições de testes em **inglês** quando adicionares testes.
- **Lint / tipos / formatação**: alinhar com ESLint/Prettier/tsc do repo afetado.

### 2. Propor correções de forma explícita

- Listar achados por severidade (**crítico** / **importante** / **menor**).
- Para cada ponto, indicar **o quê** mudar, **onde** (ficheiros/áreas) e **porquê** (risco ou qualidade).

### 3. Ajustar o código

- Aplicar as correções **acordadas com o desenho**; para mudanças grandes ou ambíguas, confirmar com o utilizador.
- Evitar deixar “só recomendações” sem corrigir o que for óbvio e seguro.

### 4. Validar

- Correr **lint** e **build** (e testes quando fizer sentido) nos pacotes **tocados**; se o monorepo tiver vários projetos, indicar claramente o que passou e o que falhou noutros roots.
- Re-verificar a aba **Problems** / diagnósticos do IDE nos ficheiros alterados.

### 5. Resposta ao utilizador (PT-BR)

- Resumo técnico curto: o que foi feito, o que foi corrigido após o review, e riscos/resíduos.
- Próximos passos opcionais (testes manuais, feature flags, docs).

## Relação com outras skills

- Para a profundidade do review, seguir também **[senior-code-reviewer](../senior-code-reviewer/SKILL.md)** (estrutura de feedback e checklist).
- Para segurança específica, **[application-security-expert](../application-security-expert/SKILL.md)** quando o fluxo tocar em auth, dados sensíveis ou superfície de ataque.

## O que não fazer

- Não encerrar implementação só com “implementei” sem review e validação mínima.
- Não alterar `.env` ou segredos sem autorização explícita do utilizador (regra global mantém-se).
