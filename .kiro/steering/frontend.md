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

## Mandatory Delegation
- **NEVER edit frontend files directly** — always delegate to the `frontend-expert` subagent via `invokeSubAgent`.

## JavaScript & React
- React with hooks (functional components only)
- Modern JavaScript (ES2022+)
- Keep bundle size small — this is a simple weather display app
- Avoid unnecessary re-renders and missing lazy loading

## HTML & Accessibility
- HTML5 semantic elements: landmarks, heading hierarchy, ARIA
- WCAG 2.2 Level AA: color contrast (4.5:1 normal, 3:1 large), keyboard navigation, focus indicators
- Respect `prefers-reduced-motion` in animations

## CSS & Responsive Design
- Mobile-first responsive design (required constraint)
- CSS Grid and Flexbox for layout
- Fluid typography with `clamp()` where appropriate
- Performant animations: `transform`/`opacity` only

## AWS Infrastructure Context
- S3 static website + CloudFront distribution (OAC, not OAI)
- Cache-Control: 15min TTL for all assets
- API Gateway REST API backend with CORS
- Query parameter caching enabled on CloudFront

## Testing
- Tests in `frontend/src/components/*.test.js` and `frontend/src/hooks/__tests__/`
- Run tests: `npm test -- --watchAll=false` from `frontend/` directory

## Shell Commands — Never Pipe Output
Run commands without piping — always use plain invocation:

✅ `npm install`
✅ `npm run build`
❌ `npm install 2>&1 | tail -5`
❌ `npm run build 2>&1 | grep error`

Never pipe command output through shell tools like `tail`, `grep`, `head`, etc.

## Operational Rules
- All changes happen in the `frontend/` directory
- Use sentence case for all user-facing text
- Mobile-responsive design is mandatory
- Validate semantic HTML and accessibility

## fast-check v4 + CRA Jest: ESM subpath import resolution

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
