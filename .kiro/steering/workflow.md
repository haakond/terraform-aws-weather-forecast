---
inclusion: always
---

# Workflow Principles

Cross-cutting development workflow principles that apply across all technologies and modules.

## Continuous Learning Loop

When fixing a bug, resolving an unforeseen issue, or discovering a gotcha during development:

1. **Backport the learning** into the relevant agent steering file (e.g., `terraform.md`, `python.md`, `security.md`)
2. **Document the pattern** using the established format:
   - The error message or symptom encountered
   - The incorrect pattern (❌) that caused the issue
   - The correct pattern (✅) that resolves it
   - A brief explanation of why it happens
3. **Scope it correctly** — add the learning to the most specific steering file that covers the topic. Create a new section if needed rather than cluttering an unrelated one.

This ensures every resolved issue permanently improves the agent's knowledge base and prevents the same mistake from recurring.

## Git Commit Scoping

When committing changes, only stage files that are directly related to the current task:

- **Never use `git add -A` or `git add .` blindly** — always review `git status` first and stage only the files you changed for the task at hand
- **Unrelated changes get their own commit** — if the working tree contains modifications from a previous task or unrelated work, commit them separately with an appropriate message
- **One concern per commit** — a commit should represent a single logical change (e.g., a bug fix, a feature, a docs update), not a mix of unrelated edits

This prevents accidental coupling of unrelated changes and keeps the git history clean and reviewable.

## CI/CD Pipeline

This repository is connected to a GitHub Actions CI/CD pipeline that automatically deploys Terraform changes on `git push` to `main`. This means:

- Pushing to `main` triggers a deployment — treat every push as a production change
- Validate Terraform (`terraform validate`) before committing
- Infrastructure changes take effect shortly after push without manual intervention
- `terraform apply` is handled by the pipeline — never run it locally

## Test Consistency

When a feature or bugfix changes existing behaviour, **always update affected tests** in the same change:

- After implementing a fix or feature, run the full test suite and identify any tests that now fail due to the behaviour change (not due to bugs in the new code)
- Stale tests — tests that assert the old, now-incorrect behaviour — must be updated to reflect the new correct behaviour
- **Never leave known stale test failures as "pre-existing"** if they were caused by your change
- If a test name no longer describes the correct behaviour, rename it (e.g., `test_per_member_auth` → `test_leader_only_auth`)
- Treat test updates as part of the same logical change, committed together with the implementation

This prevents test suites from silently drifting out of sync with the actual system behaviour.

## Test Suite Health Gate

After completing any feature or bugfix (including spec task completion), **all relevant tests must pass before the work is considered done**:

- Run the full test suite after every implementation change
- If tests fail because the implementation changed, **fix the tests** — do not change the implementation to make stale tests pass
- If tests fail because of a genuine bug introduced by the change, fix the implementation
- A feature or bugfix is not complete until the test suite is green (or failures are demonstrably pre-existing and unrelated to the current change)
- Document any intentionally skipped or deferred test fixes with a comment explaining why

## Spec Document Consistency

When making any change that touches a spec (requirements, design, or tasks), treat all three documents as a unit:

- **Requirements change** → update `design.md` to reflect the new/changed requirement, AND add a task to `tasks.md` if the spec is still in progress
- **Design change** → verify `requirements.md` has a corresponding acceptance criterion; add one if missing
- **All three files** (`requirements.md`, `design.md`, `tasks.md`) should always be consistent with each other and with the actual implementation

This prevents spec drift where the implementation diverges from the documented design.
