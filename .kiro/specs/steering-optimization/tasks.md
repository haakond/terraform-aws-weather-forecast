# Implementation Plan: Steering Optimization

## Overview

Update `.kiro/steering/` files to align with Kiro best practices: correct inclusion modes, scoped content, no duplication, and property-based tests to verify all invariants hold.

## Tasks

- [x] 1. Set up property-based test infrastructure
  - Create `tests/test_steering_properties.py` with helper functions: `steering_files()` to glob `.kiro/steering/*.md`, `parse_frontmatter(path)` to parse YAML frontmatter, and `extract_headings(path)` to extract `##`-level section headings from file body
  - Hypothesis is already in `requirements.txt` — no new dependencies needed
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 2. Write property-based tests (all 6 properties)
  - [x] 2.1 Write Property 1 test: only approved files use `inclusion: always`
    - Assert that for every steering file, if `inclusion == "always"` then `path.name in {"product.md", "workflow.md"}`
    - Tag: `# Feature: steering-optimization, Property 1: only approved files use inclusion: always`
    - _Requirements: 1.1, 2.1, 2.2_

  - [ ]* 2.2 Run Property 1 test to confirm it fails before changes (red phase)
    - Expected: fails because `specs-issue-workflow.md` and `tech.md` still have `inclusion: always`

  - [x] 2.3 Write Property 2 test: every `auto` file has unique kebab-case name and non-empty description
    - Assert `name` matches `^[a-z][a-z0-9-]*$`, `description` is non-empty, and all names are unique across auto files
    - Tag: `# Feature: steering-optimization, Property 2: every auto file has unique kebab-case name and description`
    - _Requirements: 1.4, 4.1, 4.2_

  - [x] 2.4 Write Property 3 test: every `fileMatch` file has a `fileMatchPattern`
    - Assert `fileMatchPattern` is present and is a non-empty string or non-empty list
    - Tag: `# Feature: steering-optimization, Property 3: every fileMatch file has a fileMatchPattern`
    - _Requirements: 1.5, 3.1, 3.2_

  - [x] 2.5 Write Property 4 test: no `##`-level section heading appears in more than one steering file
    - Build a `seen` dict mapping heading text → filename; assert no heading appears twice
    - Tag: `# Feature: steering-optimization, Property 4: no section heading appears in more than one steering file`
    - _Requirements: 5.1, 5.2, 5.3_

  - [x] 2.6 Write Property 5 test: each steering file maps to exactly one domain
    - Assert every `path.name` is a key in `DOMAIN_MAP`; fail with a clear message for any unmapped file
    - Tag: `# Feature: steering-optimization, Property 5: each steering file maps to exactly one domain`
    - _Requirements: 8.1, 8.2, 8.3_

  - [x] 2.7 Write Property 6 test: all steering filenames are kebab-case
    - Assert `path.stem` matches `^[a-z][a-z0-9-]*$` for every `.md` file in `.kiro/steering/`
    - Tag: `# Feature: steering-optimization, Property 6: all steering filenames are kebab-case`
    - _Requirements: 8.5_

- [x] 3. Checkpoint — run all property tests before making steering changes
  - Run `pytest tests/test_steering_properties.py -v` and confirm which tests fail (red) and which pass (green)
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Update `specs-issue-workflow.md`
  - Change `inclusion: always` → `inclusion: auto`
  - Add `name: specs-issue-workflow`
  - Add `description: Spec and GitHub issue lifecycle rules — creating issues from specs, linking requirements.md to issues, posting progress comments, and closing issues on completion. Use when creating, executing, or completing a Kiro spec.`
  - No content changes to the body
  - _Requirements: 1.3, 1.4, 2.4, 4.1, 4.2_

- [x] 5. Update `tech.md`
  - Change `inclusion: always` → `inclusion: auto`
  - Add `name: tech-stack`
  - Add `description: Tech stack reference — language runtimes, testing frameworks, IaC providers, security standards, observability config, and documentation conventions. Use when making architectural decisions, setting up new components, or verifying stack-level constraints.`
  - Remove the entire `## Frontend Testing` section (fast-check v4 + CRA Jest content)
  - Remove the entire `## Workflow` section
  - _Requirements: 1.3, 1.4, 2.3, 4.1, 4.2, 5.3, 6.2, 6.3, 8.3_

- [x] 6. Create `frontend.md`
  - Create `.kiro/steering/frontend.md` with frontmatter: `inclusion: fileMatch`, `fileMatchPattern: ["frontend/**/*.js", "frontend/**/*.jsx", "frontend/**/*.ts", "frontend/**/*.tsx", "frontend/**/*.css", "frontend/**/*.html"]`
  - Body content: the `## Frontend Testing` section moved from `tech.md` (fast-check v4 + CRA Jest ESM subpath import resolution gotcha with the `moduleNameMapper` example)
  - _Requirements: 1.2, 1.5, 3.1, 6.3, 8.1, 8.4, 8.5_

- [x] 7. Checkpoint — run all property tests after steering changes
  - Run `pytest tests/test_steering_properties.py -v` and confirm all 6 property tests pass (green)
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Close GitHub issue #9
  - Post a comment on issue #9 summarising how each requirement was met, implemented, and verified (max 3 sentences per requirement)
  - Close issue #9 via the GitHub MCP server
