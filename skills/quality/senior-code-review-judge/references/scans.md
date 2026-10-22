# Senior Code Reviewer — Mechanical Scans

Bash blocks extracted from `SKILL.md` STEP 2 to keep the skill under budget. All snippets are LOCAL-only; remote reviews use chat tools instead.

## Resolve base ref dynamically (never hardcode `origin/main`)

```bash
BASE="$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's@^origin/@@')"
BASE="${BASE:-main}"
echo "BASE: ${BASE}"
```

Two statements (not `... || echo main` on the pipeline) so the fallback evaluates `${BASE}` instead of the pipeline's exit code. Without `set -o pipefail`, `sed` succeeds on empty input and the `||` form silently leaves `BASE=""`.

Use `${BASE}` everywhere a base branch is needed (e.g., `git diff origin/${BASE}...HEAD`).

## Convention scans (added lines only; ignore comments)

```bash
ADDED="git diff --unified=0 origin/${BASE}...HEAD | grep -E '^\+' | grep -vE '^\+\+\+|^\+\s*(//|\*|#)'"

eval "$ADDED" | grep -nE ':\s*any\b[^A-Za-z]'                                          # bare `any`
eval "$ADDED" | grep -nE '\bas\s+[A-Z][A-Za-z0-9]+\b' | grep -vE '\bas (const|unknown|never)\b'  # unsafe casts
eval "$ADDED" | grep -nE '\s\|\|\s' | grep -vE 'eslint-disable|`[^`]*\|\|[^`]*`'       # `||` instead of `??`
eval "$ADDED" | grep -nE 'dangerouslySetInnerHTML'                                     # XSS surface
eval "$ADDED" | grep -nE '\bconsole\.(log|debug)\b'                                    # forgotten logs
eval "$ADDED" | grep -nE '@ts-(ignore|expect-error|nocheck)'                           # TS escape hatches
```

## Structural file-size limit (≤ 800 LOC)

Exempts test files, generated/config files, and Drizzle SQL migrations.

```bash
for f in $(git diff --name-only --diff-filter=ACMR origin/${BASE}...HEAD); do
  [ -f "$f" ] || continue
  case "$f" in
    *.spec.*|*.test.*|*.config.*|*schema.prisma|*/drizzle/*.sql|*/migrations/*.sql) continue ;;
  esac
  lines=$(wc -l < "$f")
  [ "$lines" -gt 800 ] && echo "OVER_LIMIT: $f ($lines lines)"
done
```

## [STFlow] Entry-point search (Drizzle writes)

```bash
rg "db\.(insert|update|delete)\(<table>\)" --type ts -l
rg "db\.execute\(sql" --type ts -l                                                     # raw/templated SQL
rg "from\s+['\"].*<modulePath>" --type ts -l                                           # importers
rg -i "insert into|update .* set|delete from" apps/api/drizzle --glob '*.sql'          # migrations
```

## [STFlow] Test mocking patterns

```bash
rg "overrideProvider\(DRIZZLE_PROVIDER" --type ts -l                                   # NestJS provider override
rg "vi\.mock\(['\"].*database['\"]" --type ts -l                                       # Vitest module mock
```

## DOCS-ONLY detection

```bash
DOCS_ONLY=$(git diff --name-only origin/${BASE}...HEAD | grep -vE '\.(md|mdc|txt|json|ya?ml|sh)$' | wc -l)
[ "$DOCS_ONLY" = "0" ] && echo "MODE: DOCS-ONLY (skip lint/test/build/STEP-3/STEP-4)"
```
