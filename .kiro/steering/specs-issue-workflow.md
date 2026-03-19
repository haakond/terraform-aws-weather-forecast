---
inclusion: always
---

# Spec ↔ GitHub Issue Workflow

## Team Composition

| Name | Email | GitHub Username |
|------|-------|-----------------|
| Håkon Eriksen Drange | haakondrange@gmail.com | haakond |

When the user asks for issues assigned to them, look up issues assigned to `haakond`.

## New Spec → GitHub Issue

When a new Kiro spec is created and `requirements.md` is accepted:

1. Create a GitHub issue in `haakond/terraform-aws-weather-forecast` using the contents of `requirements.md`
2. The issue body should contain the user stories and acceptance criteria from `requirements.md`
3. One `requirements.md` = one GitHub issue
4. Assign the issue to `haakond` (default assignee)
5. Set the label based on spec type:
   - Feature spec → label `enhancement`
   - Bugfix spec → label `bug`
6. Add a link reference to the GitHub issue at the top of `requirements.md`, e.g. `> GitHub Issue: https://github.com/haakond/terraform-aws-weather-forecast/issues/<number>`

**IMPORTANT**: Do not proceed to design until the GitHub issue has been created and the link added to `requirements.md`. This is a mandatory step, not optional.

## GitHub Issue → New Spec

When the user asks to create a Kiro spec from an existing GitHub issue:

1. Create the spec (requirements, design, tasks) based on the issue content
2. Once `requirements.md` is accepted, update the existing GitHub issue body to reflect the finalized requirements — do not create a new issue
3. Add a link reference to the GitHub issue at the top of `requirements.md`, e.g. `> GitHub Issue: https://github.com/haakond/terraform-aws-weather-forecast/issues/<number>`
4. Ensure the issue has the correct properties — if any are missing, set them:
   - Assignee: `haakond`
   - Label: `enhancement` for feature specs, `bug` for bugfix specs

## Spec Complete → Move Issue to Ready

When `tasks.md` has been created and accepted by the user:

1. Move the linked GitHub issue to **Ready** on the Kanban board at `https://github.com/users/haakond/projects/1/views/1` using the GitHub MCP server.

## Starting Work → Notify Issue

When beginning execution of the **first task** in a spec's `tasks.md`:

1. Post a comment on the linked GitHub issue: `🚧 Starting work on this issue.`
2. Move the issue to **In Progress** on the Kanban board at `https://github.com/users/haakond/projects/1/views/1` using the GitHub MCP server.

## Spec Completion → Close Issue

When generating tasks in `tasks.md`, always add a final task at the end:

```
- [ ] Close GitHub issue #<number>
```

When all other tasks are complete, before closing the issue:

1. Post a comment on the GitHub issue summarising how the work was completed. For each requirement in `requirements.md`, write a maximum of 3 sentences covering: how the requirement was met, how it was implemented, and how it was tested/verified.
2. Then close the corresponding GitHub issue via the GitHub MCP server.
3. Update the issue's project status to **In Review** on the Kanban board — a human will move it to Done after verifying.
4. Mark this final task as done.

## Completed Spec Guardrail

A spec is considered **locked** when all tasks in `tasks.md` are marked complete (`[x]`).

- **Never amend or add to a locked spec's `requirements.md`, `design.md`, or `tasks.md`.**
- If the user requests changes or additions to a completed spec, **always create a new spec** instead.
- Treat a completed spec the same way as a closed GitHub issue — immutable after the fact.
- If asked to modify a locked spec, explain that it's complete and offer to create a new spec for the requested change.
