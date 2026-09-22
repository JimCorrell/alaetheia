# Repository guidance

Read `README.md`, `docs/architecture/current.md`, `docs/architecture/principles.md`, and the relevant lab brief before changing code. Git-tracked documents are canonical; chat transcripts inform changes but do not silently amend the architecture.

## Current scope

Labs 001–006 and the architecture-review consolidation are authorized and implemented. The repository provides deterministic discovery, trusted local invocation, sequential reusable workflows, advisory preflight, structured domain rejection, and local run comparisons. Lab results and ADRs preserve the history; `current.md` resolves superseded behavior.

No Lab 007, supervisor, LLM integration, additional agent, remote provider, side-effecting example, persistence, or distributed runtime is authorized by this file. Keep preflight advisory, provider selection explicit, and absent-reference failures fail-fast. Do not add defaults, retries, repair, or branching without a scoped request.

## Working rules

- Prefer Function > Service > Workflow > Agent > Multi-Agent.
- Keep semantic capability identity separate from provider and implementation identity.
- Reuse LocalExecutor validation and selection checks; preserve domain rejection versus provider failure versus invalid output.
- Successful outputs must follow the data-only snapshot contract in ADR-008/current.md. Never invoke custom copying or encoding hooks to accept extra values.
- Record architectural boundary changes in an ADR and update the current reference. Annotate historical decisions instead of erasing the experiment's evidence.
- Keep Python 3.12+ compatibility and run `python -m unittest discover -s tests -v`. CI targets Python 3.12–3.14. Do not add runtime dependencies without a concrete need.

The enclosing ChatGPT project mirror's AGENTS.md and sources are read-only managed references outside this Git repository.
