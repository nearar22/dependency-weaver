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

StudioNet deployment and live lifecycle evidence are added after the reviewed source is committed and deployed.
