You are generating a file explaining a user request for an agentic workflow.

Input you will receive:
- USER_REQUEST: the raw text from the user (verbatim)

Your job:
- Reply ONLY in valid Markdown.
- Put the raw user request verbatim under “Raw user input”.
- Do not invent facts. If something is not stated, put it under Assumptions or Unknowns.
- Keep it short, concrete, and testable.
- If information is missing, record it under “Missing inputs” or “Unknowns”. Do not ask questions.
- Prefer "TBC" over guessing.

Now respond using this template and the provided USER_REQUEST:

# User Request

## Raw user input
- {{task}}

## AI interpretation
- <One short paragraph. What I think they mean. Label any guesses as ASSUMPTION.>

## What “done” means (draft)
- <If possible, define completion in 1 to 3 bullets. If not, write: TBC.>

## Success criteria (testable 1-5 outcomes)
- [ ] <Outcome 1>
- [ ] <Outcome 2>
- [ ] <Outcome 3>

## Scope
### In scope
- <bullet list>

### Out of scope
- <bullet list>
