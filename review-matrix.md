# Readiness matrix

| Requirement | Mechanism | Evidence | Status |
| --- | --- | --- | --- |
| Distinct reusable primitive | semantic plan compiles into executable DAG | README mechanism comparison | PASS |
| Complete validator scope | objective, every task, every edge and coverage checked | canonical graph test | PASS |
| Graph safety | known ids, no self or duplicate edges, deterministic cycle rejection | adversarial graph tests | PASS |
| Authorization | only frozen executor may complete each task | executor test | PASS |
| Dependency enforcement | predecessors must complete before target | ordered lifecycle test | PASS |
| Replay protection | graph inference once, completion once | replay tests | PASS |
| Exact deployed source | reviewed commit, digest and Explorer source | commit `ec6d61b`, deployment `0x23eea2...3855a` | PASS |
| Real network execution | compile and execute a live two-account plan | `scripts/live_verification.json` | PASS |
