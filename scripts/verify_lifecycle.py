import json, os, sys, time
sys.path.insert(0, os.path.dirname(__file__))
import patch_status; patch_status.apply()
from gl import make_client, load_secondary_pk, read_view
from genlayer_py import create_client, create_account
from genlayer_py.chains import studionet

TERMINAL = {"ACCEPTED", "FINALIZED", "UNDETERMINED", "CANCELED"}
def wait(client, tx):
    for _ in range(180):
        item = client.get_transaction(transaction_hash=tx); status = str(item.get("status_name") or item.get("status")); print(status, tx, flush=True)
        if status in TERMINAL:
            if status not in {"ACCEPTED", "FINALIZED"}: raise RuntimeError("Transaction ended " + status)
            return status
        time.sleep(8)
    raise TimeoutError("Transaction did not reach successful terminal status")
def write(client, address, method, args):
    tx = client.write_contract(address=address, function_name=method, args=args, value=0); wait(client, tx); return tx
def main():
    root = os.path.dirname(os.path.dirname(__file__)); address = json.load(open(os.path.join(root, "deployment.json")))["address"]
    owner_client, owner = make_client(); editor = create_account(account_private_key=load_secondary_pk()); editor_client = create_client(chain=studionet, account=editor)
    tasks = json.dumps([
        {"id":"prepare","title":"Prepare release artifact","description":"Build and test the versioned release artifact from approved source.","deliverable":"Tested versioned release artifact","executor":owner.address},
        {"id":"publish","title":"Publish release artifact","description":"Publish the tested versioned artifact to the release registry.","deliverable":"Registry publication receipt","executor":editor.address}
    ])
    txs = {}
    txs["create_plan"] = write(owner_client, address, "create_plan", ["Release delivery", "Build, test, and publish one versioned release artifact to the registry.", tasks])
    txs["weave_dependencies"] = write(owner_client, address, "weave_dependencies", ["plan-1"])
    plan = read_view(owner_client, owner, address, "get_plan", ["plan-1"])
    expected = [{"from":"prepare","to":"publish"}]
    actual = [{"from":x.get("from"),"to":x.get("to")} for x in plan.get("edges", [])]
    if actual != expected: raise RuntimeError("Unexpected live graph: " + json.dumps(plan.get("edges", [])))
    txs["complete_prepare"] = write(owner_client, address, "complete_task", ["plan-1", "prepare", "artifact://release-v1-tested"])
    txs["complete_publish"] = write(editor_client, address, "complete_task", ["plan-1", "publish", "registry://release-v1-receipt"])
    final = read_view(owner_client, owner, address, "get_plan", ["plan-1"])
    if final.get("phase") != "COMPLETE": raise RuntimeError("Live plan did not complete")
    out = {"status":"ACCEPTED","transactions":txs,"plan":{"id":final.get("id"),"phase":final.get("phase"),"completed":final.get("completed"),"graph_hash":final.get("graph_hash")},"edges":final.get("edges"),"validator_audit":final.get("validator_audit")}
    with open(os.path.join(root, "scripts", "live_verification.json"), "w", encoding="utf-8") as handle: json.dump(out, handle, indent=2)
    print(json.dumps(out, indent=2))
if __name__ == "__main__": main()
