# PowerTrace Agents

This repository uses specialized agents. When starting work, choose the smallest agent that matches the task.

## Available Agents

### Repository Analyst

Use for understanding the codebase before implementation.

Instruction file:

`agents/repository-analyst.md`

### Backend Documentation Agent

Use for documenting backend architecture, modules, functions, APIs, standards logic, and development workflows.

Instruction file:

`agents/backend-documentation-agent.md`

### Thesis Writing Agent

Use for writing, revising, structuring, and polishing the final thesis paper in Brazilian Portuguese.

Instruction file:

`agents/thesis-writing-agent.md`

## General Rule

Do not mix agent roles unless the user explicitly asks.

If the task is about code understanding, use the Repository Analyst.

If the task is about codebase documentation, use the Backend Documentation Agent.

If the task is about academic writing, use the Thesis Writing Agent.
