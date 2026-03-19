# Design Document: Steering Optimization

## Overview

This design covers the changes needed to bring all `.kiro/steering/` files into alignment with Kiro best practices. The core goal is to ensure each file uses the correct inclusion mode, covers exactly one domain, carries no duplicate content, and is as concise as possible — so the agent receives the right context at the right time without unnecessary token overhead.

The changes fall into four categories:
1. Frontmatter updates (inclusion mode, name, description, fileMatchPattern)
2. Content moves (sections migrating from one file to another)
3. File creation (new `frontend.md` for frontend-specific gotchas)
4. Content removal (deduplication and conciseness trimming within files)

---

## Architecture

The steering system is a flat directory of Markdown files under `.kiro/steering/`. Kiro reads each file's YAML frontmatter to decide when to inject it into agent context:

```
.kiro/steering/
├── product.md          → always
├── workflow.md         → always
├── python.md           → fileMatch  (**/*.py)
├── terraform.md        → fileMatch  (**/*.tf, **/*.tfvars, **/*.tftest.hcl)
├── frontend.md         → fileMatch  (NEW — frontend/**/*.{js,jsx,ts,tsx,css,html})
├── tech.md             → auto
├── structure.md        → auto       (already correct)
├── mcp.md              → auto       (already correct)
├── subagent-delegation.md → auto    (already correct)
├── specs-issue-workflow.md → auto   (was: always)
└── github-mcp.md       → manual     (already correct)
```

The two `always` files (`product.md`, `workflow.md`) are the only ones injected on every request. Everything else is either triggered by file context or retrieved on demand.

---

## Components and Interfaces

### Frontmatter Schema

Each steering file's frontmatter must conform to one of three shapes:

**always**
```yaml
---
inclusion: always
---
```

**fileMatch**
```yaml
---
inclusion: fileMatch
fileMatchPattern: "<glob>"   # or array of globs
---
```

**auto**
```yaml
---
inclusion: auto
name: <kebab-case-identifier>
description: <1–3 sentences describing content and retrieval trigger>
---
```

**manual**
```yaml
---
inclusion: manual
---
```

---

## Data Models

### File-by-File Analysis

#### `product.md`
- Current: `inclusion: always` — no name/description
- Target: `inclusion: always` — no change needed
- Content: No changes. Product context is universally needed.
- Rationale: Every agent interaction benefits from knowing what the product is.

#### `workflow.md`
- Current: `inclusion: always` — no name/description
- Target: `inclusion: always` — no change needed
- Content: No changes. Cross-cutting workflow rules (git scoping, CI/CD, test health gate, spec consistency) apply to every task.
- Rationale: These rules are not domain-specific; they govern all work.

#### `python.md`
- Current: `inclusion: fileMatch`, `fileMatchPattern: "**/*.py"` — already correct
- Target: No frontmatter change
- Content: No changes. Already scoped correctly to Python files.

#### `terraform.md`
- Current: `inclusion: fileMatch`, `fileMatchPattern: ["**/*.tf", "**/*.tfvars", "**/*.tftest.hcl"]` — already correct
- Target: No frontmatter change
- Content: No changes. Already scoped correctly to Terraform files.

#### `structure.md`
- Current: `inclusion: auto`, `name: project-structure`, `description: ...` — already correct
- Target: No change
- Content: No changes.

#### `mcp.md`
- Current: `inclusion: auto`, `name: mcp-servers`, `description: ...` — already correct
- Target: No change
- Content: No changes.

#### `subagent-delegation.md`
- Current: `inclusion: auto`, `name: subagent-delegation`, `description: ...` — already correct
- Target: No change
- Content: No changes.

#### `github-mcp.md`
- Current: `inclusion: manual` — already correct
- Target: No change
- Content: No changes. Setup instructions are only needed on explicit request.

#### `specs-issue-workflow.md`
- Current: `inclusion: always` — no name/description
- Target: `inclusion: auto`, add `name: specs-issue-workflow`, add `description`
- Content: No content changes — the rules themselves are correct, just the inclusion mode is wrong.
- Rationale: Spec/issue workflow rules are only relevant when creating or executing specs. They add noise on every other request (Terraform edits, Python debugging, etc.).
- Description: `Spec and GitHub issue lifecycle rules — creating issues from specs, linking requirements.md to issues, posting progress comments, and closing issues on completion. Use when creating, executing, or completing a Kiro spec.`

#### `tech.md`
- Current: `inclusion: always` — no name/description
- Target: `inclusion: auto`, add `name: tech-stack`, add `description`
- Content changes:
  - **Remove** the entire `## Frontend Testing` section (fast-check v4 + CRA Jest gotcha) — this moves to `frontend.md`
  - **Remove** the `## Workflow` section — these rules (`DO NOT create summary documents`, `KISS principle`) are already implied by `workflow.md` or are too vague to be useful steering
  - Remaining content (Application, Infrastructure, Security & Observability, Documentation) stays
- Rationale: Detailed tech stack info is only needed when making architectural decisions or setting up new components, not on every request. The frontend testing gotcha is only relevant when editing frontend files.
- Description: `Tech stack reference — language runtimes, testing frameworks, IaC providers, security standards, observability config, and documentation conventions. Use when making architectural decisions, setting up new components, or verifying stack-level constraints.`

#### `frontend.md` (NEW)
- Target: `inclusion: fileMatch`, `fileMatchPattern: ["frontend/**/*.js", "frontend/**/*.jsx", "frontend/**/*.ts", "frontend/**/*.tsx", "frontend/**/*.css", "frontend/**/*.html"]`
- Content: The `## Frontend Testing` section from `tech.md` (fast-check v4 + CRA Jest ESM subpath import resolution gotcha), plus a mandatory delegation rule consistent with the pattern in `python.md` and `terraform.md`.
- Rationale: Frontend-specific gotchas are only relevant when editing frontend files. Mirrors the pattern of `python.md` and `terraform.md`.

### Content Movement Summary

| Content | From | To | Reason |
|---|---|---|---|
| `## Frontend Testing` (fast-check gotcha) | `tech.md` | `frontend.md` | Only relevant when editing frontend files |
| `## Workflow` section | `tech.md` | removed | Redundant with `workflow.md`; vague |
| Inclusion mode change | `specs-issue-workflow.md` | same file | Was `always`, becomes `auto` |
| Inclusion mode change | `tech.md` | same file | Was `always`, becomes `auto` |

---

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Only approved files use `inclusion: always`

*For any* steering file in `.kiro/steering/`, if its frontmatter declares `inclusion: always`, then its filename must be one of `product.md` or `workflow.md`.

**Validates: Requirements 1.1, 2.1, 2.2**

### Property 2: Every `auto` file has a unique kebab-case name and a non-empty description

*For any* steering file with `inclusion: auto`, it must have a `name` field that matches `^[a-z][a-z0-9-]*$` and a non-empty `description` field. Furthermore, no two `auto` files may share the same `name` value.

**Validates: Requirements 1.4, 4.1, 4.2**

### Property 3: Every `fileMatch` file has a `fileMatchPattern`

*For any* steering file with `inclusion: fileMatch`, it must have a `fileMatchPattern` field that is either a non-empty string or a non-empty array of strings.

**Validates: Requirements 1.5, 3.1, 3.2**

### Property 4: No section heading appears in more than one steering file

*For any* Markdown `##`-level (or deeper) section heading, that heading text must appear in at most one steering file across the entire `.kiro/steering/` directory.

**Validates: Requirements 5.1, 5.2, 5.3**

### Property 5: Each steering file maps to exactly one domain

*For any* steering file, its content must be classifiable under a single domain from the set: {product, workflow, python, terraform, frontend, tech-stack, project-structure, mcp, subagent-delegation, specs-workflow, github-mcp}. No file may contain top-level sections belonging to two or more distinct domains.

**Validates: Requirements 8.1, 8.2, 8.3**

### Property 6: All steering filenames are kebab-case

*For any* file in `.kiro/steering/` with a `.md` extension, its filename (excluding extension) must match `^[a-z][a-z0-9-]*$`.

**Validates: Requirements 8.5**

---

## Error Handling

These are configuration files, not runtime code, so "errors" manifest as misconfiguration:

- **Missing `name` on auto file**: Agent cannot retrieve the file on demand — it becomes effectively invisible. Caught by Property 2.
- **Missing `fileMatchPattern` on fileMatch file**: Kiro may reject the file or treat it as always-included. Caught by Property 3.
- **Duplicate content**: Agent receives conflicting instructions. Caught by Property 4.
- **Wrong inclusion mode on `specs-issue-workflow.md`**: Spec/issue rules injected into every Terraform or Python session, wasting tokens. Caught by Property 1.
- **Frontend gotcha left in `tech.md`**: Frontend-specific ESM resolution instructions appear in non-frontend sessions. Caught by Property 5.

---

## Testing Strategy

### Dual Testing Approach

Both unit tests and property-based tests are used. Unit tests verify specific file states (examples); property tests verify universal invariants across all files.

### Unit Tests (Examples)

These verify the specific post-migration state of each file:

- `tech.md` has `inclusion: auto`, `name: tech-stack`, non-empty `description`
- `tech.md` does NOT contain the string `fast-check` or `pure-rand`
- `tech.md` does NOT contain a `## Workflow` section
- `specs-issue-workflow.md` has `inclusion: auto`
- `frontend.md` exists with `inclusion: fileMatch` and a `fileMatchPattern` covering `frontend/**/*.js`
- `frontend.md` contains the `fast-check` / `pure-rand` moduleNameMapper example
- `workflow.md` has `inclusion: always`
- `product.md` has `inclusion: always`
- `python.md` has `inclusion: fileMatch` and `fileMatchPattern: "**/*.py"`
- `terraform.md` has `inclusion: fileMatch` and fileMatchPattern covering `.tf`, `.tfvars`, `.tftest.hcl`
- `github-mcp.md` has `inclusion: manual`

### Property-Based Tests

Property-based testing library: **Hypothesis** (Python), since the project already uses Python + pytest.

Each property test reads all `.md` files from `.kiro/steering/`, parses their YAML frontmatter, and asserts the invariant. Tests run with `@given` strategies that generate subsets of the file list to verify the property holds for any subset, not just the full set.

Minimum 100 iterations per property test.

**Tag format**: `# Feature: steering-optimization, Property {N}: {property_text}`

#### Property Test 1: Only approved files use `inclusion: always`
```python
# Feature: steering-optimization, Property 1: only approved files use inclusion: always
APPROVED_ALWAYS = {"product.md", "workflow.md"}

def test_only_approved_files_are_always_included():
    for path in steering_files():
        fm = parse_frontmatter(path)
        if fm.get("inclusion") == "always":
            assert path.name in APPROVED_ALWAYS
```

#### Property Test 2: Every auto file has unique kebab-case name and description
```python
# Feature: steering-optimization, Property 2: every auto file has unique kebab-case name and description
def test_auto_files_have_valid_name_and_description():
    names = []
    for path in steering_files():
        fm = parse_frontmatter(path)
        if fm.get("inclusion") == "auto":
            assert re.match(r'^[a-z][a-z0-9-]*$', fm.get("name", ""))
            assert len(fm.get("description", "").strip()) > 0
            names.append(fm["name"])
    assert len(names) == len(set(names)), "auto file names must be unique"
```

#### Property Test 3: Every fileMatch file has a fileMatchPattern
```python
# Feature: steering-optimization, Property 3: every fileMatch file has a fileMatchPattern
def test_filematch_files_have_pattern():
    for path in steering_files():
        fm = parse_frontmatter(path)
        if fm.get("inclusion") == "fileMatch":
            pattern = fm.get("fileMatchPattern")
            assert pattern is not None
            assert pattern != "" and pattern != []
```

#### Property Test 4: No section heading appears in more than one file
```python
# Feature: steering-optimization, Property 4: no section heading appears in more than one steering file
def test_no_duplicate_section_headings():
    seen = {}
    for path in steering_files():
        for heading in extract_headings(path):
            assert heading not in seen, f"'{heading}' appears in both {seen[heading]} and {path.name}"
            seen[heading] = path.name
```

#### Property Test 5: Each file maps to exactly one domain
```python
# Feature: steering-optimization, Property 5: each steering file maps to exactly one domain
DOMAIN_MAP = {
    "product.md": "product", "workflow.md": "workflow",
    "python.md": "python", "terraform.md": "terraform",
    "frontend.md": "frontend", "tech.md": "tech-stack",
    "structure.md": "project-structure", "mcp.md": "mcp",
    "subagent-delegation.md": "subagent-delegation",
    "specs-issue-workflow.md": "specs-workflow",
    "github-mcp.md": "github-mcp",
}

def test_each_file_maps_to_one_domain():
    for path in steering_files():
        assert path.name in DOMAIN_MAP, f"{path.name} has no domain assignment"
```

#### Property Test 6: All steering filenames are kebab-case
```python
# Feature: steering-optimization, Property 6: all steering filenames are kebab-case
def test_steering_filenames_are_kebab_case():
    for path in steering_files():
        stem = path.stem
        assert re.match(r'^[a-z][a-z0-9-]*$', stem), f"{path.name} is not kebab-case"
```
