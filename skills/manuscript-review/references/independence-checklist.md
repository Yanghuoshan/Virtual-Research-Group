# Reviewer Independence Checklist

Independence is a property of the session and its inputs, not of the role label. A fresh session alone is not sufficient: it must also exclude the author's drafting history and self-justification.

## Prerequisites

| Requirement | Check |
|---|---|
| Fresh session | Core-verified isolated session for this task |
| No drafting history | The author's drafting conversation and self-justification excluded |
| No self-assessment | The author's own session is not used to approve its output |
| Neutral criteria | Criteria, artifacts and known limitations retained; no advocacy material |
| Task flag | `independent_review` set at task creation, not dropped on retry |

If any prerequisite fails, return a blocker and label the output as a non-independent editorial assessment. A non-independent assessment cannot satisfy a required independent review.

## What Invalidates Independence

- Reusing the author's session, or a session that saw the drafting discussion.
- Reviewing a manuscript the same session helped write.
- Carrying over prior conclusions as premises instead of re-deriving them.
- Removing the `independent_review` flag to reuse a convenient session.
- Using a different model as a substitute for a different session.

## What Does Not by Itself Establish Independence

- A `reviewer` or `critic` role label.
- A different model.
- A new task ID with the old session.
- Stating "I reviewed it objectively".

## Handling Pressure

Deadlines, prior acceptance and sunk cost do not convert a blocked independent review into a passing one. When asked to approve without isolation or evidence, return the specific missing prerequisite and the criterion that would satisfy it.

## Record

| Field | Content |
|---|---|
| Session mode and identifier | As verified by the core |
| History excluded | Drafting conversation, self-justification |
| Artifacts supplied | Versions inspected |
| Independence verdict | Independent / non-independent / blocked |
| Missing prerequisite | Exact item, if blocked |
