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
4. Assign the issue to `haakond`
5. Add a link reference to the GitHub issue at the top of `requirements.md`, e.g. `> GitHub Issue: https://github.com/haakond/terraform-aws-weather-forecast/issues/<number>`

## GitHub Issue → New Spec

When the user asks to create a Kiro spec from an existing GitHub issue:

1. Create the spec (requirements, design, tasks) based on the issue content
2. Once `requirements.md` is accepted, update the existing GitHub issue body to reflect the finalized requirements — do not create a new issue
3. Add a link reference to the GitHub issue at the top of `requirements.md`, e.g. `> GitHub Issue: https://github.com/haakond/terraform-aws-weather-forecast/issues/<number>`

## Spec Completion → Close Issue

When all tasks in a spec's `tasks.md` are marked as done, close the corresponding GitHub issue.
