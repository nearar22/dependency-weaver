# DependencyWeaver

DependencyWeaver is a reusable semantic workflow compiler for GenLayer. It turns a set of natural-language tasks into a validator-reviewed dependency graph, then enforces that graph as tasks are completed by their assigned executors.

## Why GenLayer

Whether one task truly requires another is often semantic. A task may consume a deliverable even when the descriptions use different words. GenLayer validators inspect the complete objective, every task description, every deliverable, and the proposed edge set. They accept only hard execution dependencies and reject convenience-only ordering.

## Lifecycle

1. A creator submits an objective and two to twelve tasks. Every task has a unique normalized id, description, deliverable, and nonzero executor address.
2. `weave_dependencies` runs once. Validators infer the complete edge set and ground every edge reason in the frozen task records.
3. The contract validates exact task ids, rejects self edges and duplicates, sorts the graph canonically, and runs a deterministic cycle check.
4. The plan becomes active with an immutable graph digest.
5. Only the assigned executor can complete a task, and only when every predecessor is complete.
6. Each completion stores a result reference and SHA-256 digest. The plan becomes complete only after every task is complete.

## Failure behavior

- Unknown ids, duplicate ids, zero or malformed executors, self edges, duplicate edges, and cycles fail closed.
- A model cannot directly mark a task complete or select an executor.
- Re-running graph inference is rejected.
- Early, unauthorized, and repeated completion attempts are rejected.
- Tasks with no prerequisites are exposed through `get_ready_tasks`.

## Originality comparison

Earlier workspace contracts judge evidence, policies, releases, or candidate quality. DependencyWeaver compiles semantic relationships into a deterministic DAG that actively controls which wallet may advance which task. Its reusable output is an executable dependency graph, not a verdict, score, compliance matrix, or merged document.

## Public methods

```text
create_plan(title, objective, tasks_json)
weave_dependencies(plan_id)
complete_task(plan_id, task_id, result_ref)
get_plan(plan_id)
get_ready_tasks(plan_id)
list_plans(start)
```

## Verify

```text
gltest tests -v
genvm-lint contracts/contract.py
```

## Verified StudioNet deployment

- Contract: `0x0261D420224Ff2631F5b24AC1FC1fba9Ed4aaABb`
- Deployment transaction: `0x23eea2669dc9754386089d10130c2d2f5e2b805ce34744bb333274a37243855a`
- Live dependency inference: `0xff135cd504f64ee4b030285167b5bbd63499eab9e7c9653e1b125442b63e5b5e`
- Final task completion: `0xcb2b865c852462b76fa6becdfe9f5bf9eedb44c76bfc2132297601e3afc1a218`
- Reviewed source commit: `ec6d61b26efc16a4be6fca7e6ce18ef468715e38`
- Contract SHA-256: `32b0af0abfa60e6a58fe01d0e7a5e5b799b37aabfbe9ee3686fa503088216f71`

The live plan used two assigned StudioNet executors. Validators inferred `prepare -> publish`; both task completions reached `ACCEPTED`, and `plan-1` reached `COMPLETE` with two completed tasks.
