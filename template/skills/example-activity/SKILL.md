---
name: <activity>
description: <What it does + literal trigger phrases the user would say, in quotes and in the USER'S language. Include colloquial variants — the description alone decides whether the skill fires.>
---

# <Activity>

<What this skill does, one sentence.>

## Connection & session bootstrap
1. **Working inside the agent repo** (a `local/config.json` exists in the working directory) → read it. If the repo is present but the file is missing, offer to run the **<agent>-setup** skill.
2. **Anywhere else** (claude.ai, mobile app, or Claude Code with the plugin installed in another folder) → check Claude memory for the config. If missing, ask the user once and save it to memory.

<If there's a backend: one context call per conversation; cache it; if it returns the user's personal rules, follow them for the whole session.>

## Flows
### Flow 1 — <typical case>
<User input → steps → output. Show the expected response format.>

## Rules
- <Never guess X; on ambiguity ask, showing the options.>
- <Confirm before bulk operations.>

## Error handling
- **Config not found**: offer <agent>-setup.
- <Domain-specific errors.>
