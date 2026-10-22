---
name: job-search
description: Search technology jobs and relevant recruiters using the professional profile provided in the session or ai-memory. Use when the user wants job opportunities, recruiters, or both.

disable-model-invocation: true
icon: briefcase
color: blue
---

# Job search (TI vacancies and recruiters)

## Objetivo

Encontrar oportunidades profissionais atuais e recrutadores relevantes para o perfil do usuário, sem inventar informações e sem transformar a busca em uma lista enorme. Não mostre recrutadores que eu ja tenho conectado e que vc ja tenha indicado, quero sempre novas vagas e recrutadores, antes de pegar a vaga confira se ela esta valida ainda.

Sempre retornar no máximo:
- 10 vagas
- 10 recrutadores

Se houver menos resultados realmente relevantes, retornar menos. Nunca preencher a lista com resultados fracos apenas para chegar a 10.

## Professional profile source

Do **not** embed a fixed personal profile in this skill.

Before searching, obtain the active professional profile from, in order:

1. The current session (what the user states now)
2. Project or user ai-memory pages the user points to
3. A short clarifying question if profile data is still missing

Use only skills, stack, seniority, languages, and location constraints
that are present in that profile context. Do not invent seniority,
certifications, languages, or experience.


## Regras de pesquisa

### 1. Pesquisar vagas atuais

Pesquisar na web por vagas abertas e recentes relacionadas ao perfil.

Priorizar:
1. Backend Engineer
2. Software Engineer
3. Full Stack Engineer
4. Node.js / TypeScript Engineer
5. NestJS / React / React Native quando houver aderência
6. Go Engineer
7. AI Engineer / AI Software Engineer
8. AI Agent Engineer / LLM Engineer
9. Applied AI / AI Platform Engineer
10. Solutions/Platform Engineer quando houver forte aderência técnica

Combinar termos de busca em português e inglês.

Dar preferência a:
- vagas publicadas recentemente;
- vagas ainda abertas;
- contratação CLT/PJ ou equivalente quando claramente informado;
- remoto ou localização compatível com o usuário;
- empresas e páginas de carreira identificáveis;
- vagas cujo stack e responsabilidades tenham aderência real ao perfil.

Evitar:
- vagas expiradas;
- resultados duplicados;
- agregadores que não permitem identificar a vaga original quando houver uma fonte primária;
- vagas genéricas de TI sem relação com o perfil;
- vagas que exijam tecnologias completamente fora do perfil sem nenhuma aderência relevante.

### 2. Pesquisar recrutadores

Pesquisar profissionais que atuem publicamente como:
- Tech Recruiter
- Talent Acquisition
- Technical Recruiter
- IT Recruiter
- Engineering Recruiter
- Talent Partner
- People/Recruitment especializado em tecnologia

Priorizar recrutadores que:
- trabalham atualmente com contratação de tecnologia;
- recrutam para empresas compatíveis com o perfil;
- publicam vagas de engenharia/software/IA;
- estejam no Brasil ou trabalhem com vagas remotas que aceitem profissionais no Brasil.

Não coletar nem expor dados pessoais privados. Usar somente informações profissionais públicas.

### 3. Validação

Para cada resultado, confirmar na fonte encontrada:
- título;
- empresa;
- localização/remoto;
- data ou indicação de atualidade, quando disponível;
- link da fonte;
- por que é relevante para o perfil.

Se não for possível confirmar uma informação, escrever "não informado" em vez de inferir.

### 4. Deduplicação

Não mostrar a mesma vaga mais de uma vez mesmo que apareça em vários sites.

Quando houver uma página oficial da empresa para a mesma vaga, preferir a fonte oficial.

## Formato da resposta

Começar com:

"Encontrei X vagas e Y recrutadores relevantes."

### Vagas

Tabela:

| # | Vaga | Empresa | Local/Remoto | Aderência | Fonte |
|---|---|---|---|---|---|

Em "Aderência", usar uma descrição curta e factual, por exemplo:
- "Node.js + TypeScript + AWS"
- "AI Agents + LLM + Python"
- "Backend + sistemas distribuídos"

Não usar notas, estrelas ou ranking.

### Recrutadores

Tabela:

| # | Recrutador | Cargo | Empresa | Foco | Perfil |
|---|---|---|---|---|---|

No campo "Foco", indicar o tipo de contratação observado.

## Importante

- Não inventar vagas, recrutadores, empresas, datas ou requisitos.
- Não afirmar que uma vaga está aberta sem evidência atual.
- Não apresentar uma vaga como "melhor" ou "mais indicada"; apenas explicar a aderência factual.
- Não fazer contato, candidatura ou envio de mensagens automaticamente.
- A finalidade desta skill é pesquisar e apresentar oportunidades para o usuário decidir o que fazer.
- Se a pesquisa encontrar muitas opções, limitar estritamente a 10 vagas e 10 recrutadores.
- Se uma busca não encontrar resultados suficientes, fazer novas consultas com termos equivalentes antes de concluir.
- Registrar a data da pesquisa no final.
