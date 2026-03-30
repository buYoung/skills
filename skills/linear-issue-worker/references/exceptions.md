# Exception Handling

## Target Location file doesn't exist

1. Post a comment noting the expected file was not found
2. Search nearby directories for the most logical placement
3. If confident, proceed and note the deviation. If unsure, ask the user

## Library / dependency not available

1. Check if it can be installed (`npm install`, `pip install`, etc.)
2. If reasonable, install and note in the completion comment
3. If it's a major or unexpected dependency, ask the user

## Done Criteria is ambiguous or impossible

1. Post a comment stating your interpretation
2. Proceed based on that interpretation
3. Flag it clearly in the completion comment

## Blocker discovered mid-work

1. Post a comment explaining the blocker
2. Transition the issue back to Todo using `state: "unstarted"`
3. Move to the next available sub-issue
4. If nothing else is available, report to the user and stop

## All remaining sub-issues are blocked (deadlock)

1. Report the dependency graph to the user
2. Suggest which blocker to resolve manually or which dependency to remove
