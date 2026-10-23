# ESLint Preset - Copy/Paste Ready

Drop this into any TypeScript project to enforce the hard limits and TS strict patterns documented in [SKILL.md](SKILL.md).

## Required dev dependencies

```bash
pnpm add -D \
  eslint \
  @typescript-eslint/parser \
  @typescript-eslint/eslint-plugin \
  eslint-plugin-import \
  eslint-plugin-promise \
  eslint-plugin-sonarjs \
  eslint-plugin-unicorn \
  eslint-config-prettier \
  eslint-plugin-prettier \
  prettier
```

For React projects also:

```bash
pnpm add -D eslint-plugin-react eslint-plugin-react-hooks eslint-plugin-jsx-a11y
```

## `.eslintrc.cjs` - base preset (Node/TS service)

```js
module.exports = {
  root: true,
  parser: '@typescript-eslint/parser',
  parserOptions: {
    ecmaVersion: 2023,
    sourceType: 'module',
    project: './tsconfig.json',
  },
  env: { node: true, es2023: true },
  plugins: ['@typescript-eslint', 'import', 'promise', 'sonarjs', 'unicorn', 'prettier'],
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended-type-checked',
    'plugin:@typescript-eslint/strict-type-checked',
    'plugin:import/recommended',
    'plugin:import/typescript',
    'plugin:promise/recommended',
    'plugin:sonarjs/recommended-legacy',
    'plugin:unicorn/recommended',
    'prettier',
    'plugin:prettier/recommended',
  ],
  settings: {
    'import/resolver': { typescript: { alwaysTryTypes: true } },
  },
  rules: {
    // Hard size limits
    'max-lines': ['error', { max: 500, skipBlankLines: true, skipComments: true }],
    'max-lines-per-function': ['error', { max: 40, skipBlankLines: true, skipComments: true }],
    'max-params': ['error', 4],
    'max-depth': ['error', 3],
    'max-statements': ['error', 25],

    // Complexity
    'complexity': ['error', 10],
    'sonarjs/cognitive-complexity': ['error', 15],
    'sonarjs/no-duplicate-string': ['error', { threshold: 4 }],

    // TS strictness
    '@typescript-eslint/no-explicit-any': 'error',
    '@typescript-eslint/no-unsafe-assignment': 'error',
    '@typescript-eslint/no-unsafe-member-access': 'error',
    '@typescript-eslint/no-unsafe-call': 'error',
    '@typescript-eslint/no-unsafe-return': 'error',
    '@typescript-eslint/no-non-null-assertion': 'error',
    '@typescript-eslint/consistent-type-imports': 'error',
    '@typescript-eslint/no-floating-promises': 'error',
    '@typescript-eslint/no-misused-promises': 'error',
    '@typescript-eslint/prefer-readonly': 'error',
    '@typescript-eslint/prefer-nullish-coalescing': 'error',
    '@typescript-eslint/strict-boolean-expressions': ['error', { allowNullableObject: false }],
    '@typescript-eslint/switch-exhaustiveness-check': 'error',

    // Ban || for defaults (use ??)
    'no-restricted-syntax': [
      'error',
      {
        selector: "LogicalExpression[operator='||']",
        message: 'Use ?? instead of || for default values to preserve falsy values (0, "", false).',
      },
      {
        selector: 'TSEnumDeclaration',
        message: 'Use a const object + literal union type instead of enum.',
      },
    ],

    // Imports
    'import/order': [
      'error',
      {
        groups: ['builtin', 'external', 'internal', 'parent', 'sibling', 'index', 'type'],
        'newlines-between': 'always',
        alphabetize: { order: 'asc', caseInsensitive: true },
      },
    ],
    'import/no-default-export': 'error',
    'import/no-cycle': 'error',
    'import/no-duplicates': 'error',

    // Promises
    'promise/always-return': 'error',
    'promise/catch-or-return': 'error',

    // Quality
    'no-console': 'error',
    'no-debugger': 'error',
    'no-eval': 'error',
    'no-implied-eval': 'error',
    'no-new-wrappers': 'error',
    'no-param-reassign': ['error', { props: true }],
    'no-return-await': 'error',
    'eqeqeq': ['error', 'always', { null: 'ignore' }],
    'prefer-const': 'error',
    'object-shorthand': 'error',
    'no-nested-ternary': 'error',
    'no-unneeded-ternary': 'error',

    // Unicorn (curated)
    'unicorn/filename-case': ['error', { case: 'kebabCase' }],
    'unicorn/no-null': 'off',
    'unicorn/prevent-abbreviations': 'off',
    'unicorn/no-array-reduce': 'off',
  },
  overrides: [
    {
      files: ['**/*.spec.ts', '**/*.spec.tsx', '**/*.test.ts', '**/*.test.tsx'],
      rules: {
        'max-lines-per-function': 'off',
        'sonarjs/no-duplicate-string': 'off',
        '@typescript-eslint/no-non-null-assertion': 'off',
      },
    },
    {
      files: ['**/index.ts'],
      rules: { 'import/no-default-export': 'off' },
    },
  ],
  ignorePatterns: ['dist', 'build', 'coverage', 'node_modules', '*.config.js', '*.config.cjs'],
};
```

## React additions

Append to `extends`:

```js
'plugin:react/recommended',
'plugin:react/jsx-runtime',
'plugin:react-hooks/recommended',
'plugin:jsx-a11y/recommended',
```

Append to `plugins`: `'react', 'react-hooks', 'jsx-a11y'`.

Append to `settings`:

```js
react: { version: 'detect' },
```

Append to `rules`:

```js
'react/prop-types': 'off',                    // we use TS
'react/react-in-jsx-scope': 'off',            // React 17+
'react/jsx-no-leaked-render': 'error',
'react/jsx-no-useless-fragment': 'error',
'react/self-closing-comp': 'error',
'react-hooks/rules-of-hooks': 'error',
'react-hooks/exhaustive-deps': 'error',
'jsx-a11y/anchor-is-valid': 'error',
'jsx-a11y/click-events-have-key-events': 'error',
```

## Prettier `.prettierrc.cjs`

```js
module.exports = {
  semi: true,
  singleQuote: true,
  trailingComma: 'all',
  printWidth: 100,
  tabWidth: 2,
  arrowParens: 'always',
  endOfLine: 'lf',
};
```

## tsconfig.json - strict baseline

```json
{
  "compilerOptions": {
    "target": "ES2023",
    "lib": ["ES2023"],
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true,
    "exactOptionalPropertyTypes": true,
    "noFallthroughCasesInSwitch": true,
    "noPropertyAccessFromIndexSignature": true,
    "noImplicitReturns": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "esModuleInterop": true,
    "forceConsistentCasingInFileNames": true,
    "skipLibCheck": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "verbatimModuleSyntax": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist", "build", "coverage"]
}
```

## CI integration

```yaml
- run: pnpm install --frozen-lockfile
- run: pnpm lint --max-warnings 0
- run: pnpm typecheck
- run: pnpm test --run
- run: pnpm audit --prod
```

## Pre-commit (Husky + lint-staged)

```json
{
  "lint-staged": {
    "*.{ts,tsx,js,jsx}": ["eslint --fix --max-warnings 0", "prettier --write"]
  }
}
```

## Per-project tweaks

Some thresholds are environment-dependent:
- Spec files: relax `max-lines-per-function` (long describes are fine).
- Generated code (`*.gen.ts`): exclude entirely via `ignorePatterns`.
- Migration files: exclude (they accumulate).

Document any deviation from this preset in `docs/quality-standards.md`.
