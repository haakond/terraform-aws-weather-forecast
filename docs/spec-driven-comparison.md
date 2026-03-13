# Spec vs. Vibe — How Tools Compare

## Version 1: Detailed Comparison Table

| | Kiro | Cursor | Claude Code | Copilot (VS Code) | Windsurf |
|---|---|---|---|---|---|
| Approach | Native spec workflow baked into IDE | Plan Mode (bolt-on) | Plan Mode (bolt-on) | Plan agent + Spec Kit (external) | Planning Mode (conversational) |
| Phases | Requirements → Design → Tasks (or Design-first) | Prompt → Plan → Execute | Prompt → Plan → Execute | Discovery → Alignment → Design → Refine | Prompt → Step breakdown → Execute |
| Artifacts | `requirements.md`, `design.md`, `tasks.md` — persisted in repo | Markdown plan (session-scoped) | User-managed spec files | Spec Kit generates files externally | None |
| Requirements format | EARS notation (WHEN/SHALL) | Free-form | Free-form | Free-form | Free-form |
| Task tracking | Built-in with status and incremental execution | Checkboxes in plan UI | Manual | Checkboxes (no cross-session) | Step-by-step progress only |

**Takeaway:** Kiro is the only IDE where specs are a first-class, persistent, structured workflow — everyone else bolted on a "think before you code" step.

---

## Version 2: Simplified Visual Layout

Three categories instead of five columns — group tools by how they handle structured development.

### Native Spec Workflow

**Kiro**

- ✅ Requirements → Design → Tasks as IDE-native phases
- ✅ EARS notation for testable requirements
- ✅ Persistent artifacts versioned in repo
- ✅ Built-in task tracking with incremental execution
- ✅ Design-first or Requirements-first variants

### Bolt-On Plan Mode

**Cursor** · **Claude Code** · **Windsurf**

- ⚠️ "Think before you code" step — not a spec system
- ⚠️ Plans are session-scoped or conversational
- ⚠️ No formal requirements format
- ⚠️ No persistent design artifacts
- ⚠️ Task tracking limited to checkboxes or step progress

### External Tooling Required

**VS Code + Copilot** (via GitHub Spec Kit)

- ⚠️ Spec Kit adds structure but lives outside the IDE
- ⚠️ Generates `spec.md`, `plan.md`, `tasks.md` as add-on
- ⚠️ No cross-session task tracking
- ⚠️ Free-form requirements, no enforced notation

### The Point

> Kiro ships spec-driven development as a core product feature.
> Everyone else offers planning as an afterthought — or outsources it to external tools.
