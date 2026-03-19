# Requirements Document

## Introduction

This feature optimizes the existing Kiro steering files in `.kiro/steering/` to align with Kiro's official best practices. The goal is to ensure each steering file uses the correct `inclusion` mode (`always`, `fileMatch`, or `auto`), has appropriately scoped content, avoids redundancy, and is structured so the agent receives the right context at the right time — without overloading every request with irrelevant information.

The current steering setup has several files using `inclusion: always` that contain content better suited to `fileMatch` or `auto` mode, files with mixed concerns that should be split or scoped, and content in `always`-included files that is only relevant in specific coding contexts.

## Glossary

- **Steering_System**: The Kiro agent steering system that reads `.kiro/steering/*.md` files and injects them into agent context.
- **Inclusion_Mode**: The frontmatter field controlling when a steering file is injected — one of `always`, `fileMatch`, or `auto`.
- **Always_File**: A steering file with `inclusion: always` — injected into every agent request regardless of context.
- **FileMatch_File**: A steering file with `inclusion: fileMatch` and a `fileMatchPattern` — injected only when matching files are open or referenced.
- **Auto_File**: A steering file with `inclusion: auto`, a `name`, and a `description` — injected by the agent when it determines the content is relevant.
- **Context_Overhead**: Unnecessary tokens consumed by injecting irrelevant steering content into agent requests.

---

## Requirements

### Requirement 1: Correct Inclusion Mode Assignment

**User Story:** As a developer, I want each steering file to use the most appropriate inclusion mode, so that the agent receives relevant context without unnecessary overhead on every request.

#### Acceptance Criteria

1. THE Steering_System SHALL use `inclusion: always` only for files whose content is relevant to every single agent interaction (e.g., product context, core workflow rules, team identity).
2. THE Steering_System SHALL use `inclusion: fileMatch` for files whose content is only relevant when specific file types are open or being edited.
3. THE Steering_System SHALL use `inclusion: auto` for files whose content is situationally relevant and can be described with a short name and description for agent-driven retrieval.
4. WHEN a steering file uses `inclusion: auto`, THE Steering_System SHALL include a `name` field (kebab-case) and a `description` field that clearly describes when the file should be used.
5. WHEN a steering file uses `inclusion: fileMatch`, THE Steering_System SHALL include a `fileMatchPattern` field with a valid glob pattern.

### Requirement 2: Reduce Always-Included Context Overhead

**User Story:** As a developer, I want to minimize the number of `always`-included steering files, so that routine agent requests are not burdened with irrelevant technical detail.

#### Acceptance Criteria

1. THE Steering_System SHALL limit `inclusion: always` to files containing information the agent needs on every request without exception.
2. WHEN a steering file currently uses `inclusion: always` but contains content only relevant to specific file types or tasks, THE Steering_System SHALL change its inclusion mode to `fileMatch` or `auto` as appropriate.
3. THE Steering_System SHALL ensure `tech.md` uses `inclusion: auto` because its detailed tech stack and frontend testing gotchas are not needed on every request.
4. THE Steering_System SHALL ensure `specs-issue-workflow.md` uses `inclusion: auto` because its content is only relevant when working with specs or GitHub issues.

### Requirement 3: File-Specific Steering Uses fileMatch

**User Story:** As a developer, I want language- and tool-specific steering files to only activate when relevant files are open, so that Python rules don't appear in Terraform sessions and vice versa.

#### Acceptance Criteria

1. THE Steering_System SHALL ensure `python.md` uses `inclusion: fileMatch` with `fileMatchPattern: "**/*.py"`.
2. THE Steering_System SHALL ensure `terraform.md` uses `inclusion: fileMatch` with a pattern matching `**/*.tf`, `**/*.tfvars`, and `**/*.tftest.hcl`.
3. WHEN no matching files are open or referenced, THE Steering_System SHALL NOT inject `python.md` or `terraform.md` into agent context.

### Requirement 4: Auto-Included Files Have Descriptive Metadata

**User Story:** As a developer, I want `auto`-included steering files to have clear names and descriptions, so that the agent can accurately decide when to retrieve them.

#### Acceptance Criteria

1. WHEN a steering file uses `inclusion: auto`, THE Steering_System SHALL include a `name` field that is unique across all steering files and uses kebab-case format.
2. WHEN a steering file uses `inclusion: auto`, THE Steering_System SHALL include a `description` field of one to three sentences describing the file's content and the situations in which it should be retrieved.
3. THE Steering_System SHALL ensure `structure.md` uses `inclusion: auto` with a description referencing project layout and file organization.
4. THE Steering_System SHALL ensure `mcp.md` uses `inclusion: auto` with a description referencing MCP server selection and configuration.
5. THE Steering_System SHALL ensure `subagent-delegation.md` uses `inclusion: auto` with a description referencing subagent routing and delegation rules.
6. THE Steering_System SHALL ensure `github-mcp.md` uses `inclusion: manual` since it contains setup instructions only needed on explicit request.

### Requirement 5: No Duplicate or Redundant Content Across Files

**User Story:** As a developer, I want steering file content to be non-redundant, so that the agent does not receive conflicting or repeated instructions.

#### Acceptance Criteria

1. THE Steering_System SHALL ensure each steering concern appears in exactly one file.
2. WHEN content in one steering file duplicates content in another, THE Steering_System SHALL consolidate it into the most appropriate file and remove the duplicate.
3. THE Steering_System SHALL ensure `tech.md` does not duplicate content already present in `python.md` or `terraform.md`.

### Requirement 6: Always-Included Files Remain Concise

**User Story:** As a developer, I want `always`-included steering files to be concise and focused, so that they do not consume excessive context on every agent request.

#### Acceptance Criteria

1. THE Steering_System SHALL ensure each `always`-included file contains only high-signal, universally applicable rules.
2. WHEN an `always`-included file contains sections that are only relevant in specific coding contexts (e.g., language-specific gotchas, tool setup instructions), THE Steering_System SHALL move those sections to a more appropriately scoped file.
3. THE Steering_System SHALL ensure `tech.md` has its frontend testing gotcha section (`fast-check v4 + CRA Jest`) moved to a `fileMatch`-scoped file matching frontend file patterns, since it is only relevant when working on frontend code.
4. THE Steering_System SHALL ensure `workflow.md` remains `inclusion: always` as it contains universally applicable development workflow rules.
5. THE Steering_System SHALL ensure `product.md` remains `inclusion: always` as it contains product context needed on every request.
