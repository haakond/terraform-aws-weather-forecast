---
inclusion: fileMatch
fileMatchPattern:
  - "frontend/**/*.js"
  - "frontend/**/*.jsx"
  - "frontend/**/*.ts"
  - "frontend/**/*.tsx"
  - "frontend/**/*.css"
  - "frontend/**/*.html"
---

# Frontend

## Frontend Testing

### fast-check v4 + CRA Jest: ESM subpath import resolution

**Symptom**: `SyntaxError: Cannot use import statement outside a module` or `Cannot find module 'pure-rand/generator/...'` when using `require('fast-check')` in Jest tests under Create React App.

**Root cause**: fast-check v4 ships its `"main"` field pointing to an ESM bundle. The CJS build lives at `lib/cjs/fast-check.js` but itself uses `require('pure-rand/<subpath>')` — and CRA's Jest resolver does not honour the `exports` field's `require` condition for subpath imports.

❌ Incorrect — Jest can't resolve the ESM entry or the CJS subpath imports automatically:
```json
// package.json — no jest config
```

✅ Correct — add `moduleNameMapper` in `package.json` to redirect both fast-check and all pure-rand subpaths to their CJS files:
```json
"jest": {
  "moduleNameMapper": {
    "^fast-check$": "<rootDir>/node_modules/fast-check/lib/cjs/fast-check.js",
    "^pure-rand/(.*)$": "<rootDir>/node_modules/pure-rand/lib/$1.js"
  }
}
```

This works without ejecting CRA and requires no Babel transform changes.
