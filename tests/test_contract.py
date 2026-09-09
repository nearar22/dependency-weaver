import json, sys

CONTRACT = "contracts/contract.py"
def addr(value): return "0x" + bytes(value).hex()
def task_data(alice, bob):
    return json.dumps([
        {"id":"collect","title":"Collect dataset","description":"Collect and normalize the approved training records.","deliverable":"Normalized dataset artifact", "executor":addr(alice)},
        {"id":"train","title":"Train model","description":"Train the model using the normalized dataset artifact.","deliverable":"Versioned model checkpoint", "executor":addr(bob)},
        {"id":"evaluate","title":"Evaluate model","description":"Evaluate the versioned checkpoint against the test suite.","deliverable":"Evaluation report with metrics", "executor":addr(alice)},
    ])
def graph(): return json.dumps({"edges":[
    {"from":"collect","to":"train","reason":"Training consumes the normalized dataset artifact."},
    {"from":"train","to":"evaluate","reason":"Evaluation requires the versioned model checkpoint."},
]})
def enable_consensus(contract, monkeypatch):
    module = sys.modules[contract.__class__.__module__]
    monkeypatch.setattr(module.gl.eq_principle, "prompt_non_comparative", lambda fn, **_kwargs: fn())
def setup(contract, vm, alice, bob):
    vm.sender = alice
    return contract.create_plan("Model delivery", "Produce and evaluate a model from a normalized approved dataset.", task_data(alice, bob))

def test_task_ids_and_executor_addresses_are_validated(direct_vm, direct_deploy, direct_alice, direct_bob):
    c = direct_deploy(CONTRACT); direct_vm.sender = direct_alice
    duplicate = json.loads(task_data(direct_alice, direct_bob)); duplicate[1]["id"] = "COLLECT"
    with direct_vm.expect_revert("unique lowercase identifiers"): c.create_plan("Bad plan", "A sufficiently detailed workflow objective for testing.", json.dumps(duplicate))
    invalid = json.loads(task_data(direct_alice, direct_bob)); invalid[0]["executor"] = "alice"
    with direct_vm.expect_revert("valid nonzero executor"): c.create_plan("Bad plan", "A sufficiently detailed workflow objective for testing.", json.dumps(invalid))

def test_weave_stores_canonical_graph_and_full_validator_audit(direct_vm, direct_deploy, direct_alice, direct_bob, monkeypatch):
    c = direct_deploy(CONTRACT); enable_consensus(c, monkeypatch); pid = setup(c, direct_vm, direct_alice, direct_bob); direct_vm.mock_llm("DEPENDENCYWEAVER", graph()); result = c.weave_dependencies(pid); direct_vm.clear_mocks()
    assert result["phase"] == "ACTIVE" and [x["to"] for x in result["edges"]] == ["evaluate", "train"]
    assert result["validator_audit"] == {"objective":"checked","every_task":"checked","every_edge":"checked","coverage":"checked"}

def test_unknown_self_duplicate_and_cycle_edges_fail_closed(direct_vm, direct_deploy, direct_alice, direct_bob, monkeypatch):
    c = direct_deploy(CONTRACT); enable_consensus(c, monkeypatch)
    cases = [
        ({"edges":[{"from":"ghost","to":"train","reason":"This unknown source must be rejected."}]}, "unknown task"),
        ({"edges":[{"from":"train","to":"train","reason":"A self dependency must be rejected."}]}, "Self dependency"),
        ({"edges":[{"from":"collect","to":"train","reason":"First duplicate dependency reason."},{"from":"collect","to":"train","reason":"Second duplicate dependency reason."}]}, "Duplicate dependency"),
        ({"edges":[{"from":"collect","to":"train","reason":"Training requires collected data."},{"from":"train","to":"evaluate","reason":"Evaluation requires the trained model."},{"from":"evaluate","to":"collect","reason":"This creates an invalid workflow cycle."}]}, "contains a cycle"),
    ]
    for payload, message in cases:
        pid = setup(c, direct_vm, direct_alice, direct_bob); direct_vm.mock_llm("DEPENDENCYWEAVER", json.dumps(payload))
        with direct_vm.expect_revert(message): c.weave_dependencies(pid)
        direct_vm.clear_mocks(); assert c.get_plan(pid)["phase"] == "DRAFT"

def test_only_assigned_executor_can_complete_ready_task(direct_vm, direct_deploy, direct_alice, direct_bob, monkeypatch):
    c = direct_deploy(CONTRACT); enable_consensus(c, monkeypatch); pid = setup(c, direct_vm, direct_alice, direct_bob); direct_vm.mock_llm("DEPENDENCYWEAVER", graph()); c.weave_dependencies(pid); direct_vm.clear_mocks()
    direct_vm.sender = direct_bob
    with direct_vm.expect_revert("assigned executor"): c.complete_task(pid, "collect", "dataset://normalized-v1")
    direct_vm.sender = direct_alice; receipt = c.complete_task(pid, "collect", "dataset://normalized-v1"); assert receipt["status"] == "COMPLETE"

def test_prerequisites_block_early_completion_and_unlock_in_order(direct_vm, direct_deploy, direct_alice, direct_bob, monkeypatch):
    c = direct_deploy(CONTRACT); enable_consensus(c, monkeypatch); pid = setup(c, direct_vm, direct_alice, direct_bob); direct_vm.mock_llm("DEPENDENCYWEAVER", graph()); c.weave_dependencies(pid); direct_vm.clear_mocks()
    assert [x["id"] for x in c.get_ready_tasks(pid)] == ["collect"]
    direct_vm.sender = direct_bob
    with direct_vm.expect_revert("prerequisites"): c.complete_task(pid, "train", "model://checkpoint-v1")
    direct_vm.sender = direct_alice; c.complete_task(pid, "collect", "dataset://normalized-v1"); assert [x["id"] for x in c.get_ready_tasks(pid)] == ["train"]
    direct_vm.sender = direct_bob; c.complete_task(pid, "train", "model://checkpoint-v1"); assert [x["id"] for x in c.get_ready_tasks(pid)] == ["evaluate"]

def test_full_execution_reaches_complete_and_replay_fails(direct_vm, direct_deploy, direct_alice, direct_bob, monkeypatch):
    c = direct_deploy(CONTRACT); enable_consensus(c, monkeypatch); pid = setup(c, direct_vm, direct_alice, direct_bob); direct_vm.mock_llm("DEPENDENCYWEAVER", graph()); c.weave_dependencies(pid); direct_vm.clear_mocks()
    direct_vm.sender = direct_alice; c.complete_task(pid, "collect", "dataset://normalized-v1")
    direct_vm.sender = direct_bob; c.complete_task(pid, "train", "model://checkpoint-v1")
    direct_vm.sender = direct_alice; final = c.complete_task(pid, "evaluate", "report://evaluation-v1"); assert final["plan_phase"] == "COMPLETE"
    with direct_vm.expect_revert("Plan is not active"): c.complete_task(pid, "evaluate", "report://evaluation-v2")

def test_dependencies_can_only_be_woven_once(direct_vm, direct_deploy, direct_alice, direct_bob, monkeypatch):
    c = direct_deploy(CONTRACT); enable_consensus(c, monkeypatch); pid = setup(c, direct_vm, direct_alice, direct_bob); direct_vm.mock_llm("DEPENDENCYWEAVER", graph()); c.weave_dependencies(pid); direct_vm.clear_mocks()
    with direct_vm.expect_revert("only be woven once"): c.weave_dependencies(pid)
