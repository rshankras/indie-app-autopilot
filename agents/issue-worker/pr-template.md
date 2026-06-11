# PR body template (issue-worker)

```markdown
Closes #{{ISSUE_NUMBER}}

## What changed
{{ONE_PARAGRAPH_SUMMARY}}

## Acceptance criteria
- [x] {{CRITERION_1}} — verified by `{{TEST_NAME_1}}`
- [x] {{CRITERION_2}} — verified by `{{TEST_NAME_2}}`

## Tests
- Full suite: {{N}} passed, 0 failed ({{TEST_COMMAND}})
- New tests: {{LIST_OF_NEW_TESTS}}

## Screenshots
| Before | After |
|---|---|
| {{BEFORE_IMG}} | {{AFTER_IMG}} |

_Omit the screenshots section for non-UI changes._

## Out of scope / noticed along the way
{{NOTES_OR_NONE}}

---
🤖 Opened by issue-worker · human review required before merge
```
