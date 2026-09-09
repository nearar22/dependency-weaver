import os, urllib.request
from genlayer_py import create_client, create_account
from genlayer_py.chains import studionet

_opener = urllib.request.build_opener()
_opener.addheaders = [("User-Agent", "Mozilla/5.0")]
urllib.request.install_opener(_opener)


def load_pk():
    value = os.environ.get("GENLAYER_PRIVATE_KEY", "").strip()
    if not value:
        shared = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
        with open(shared, encoding="utf-8") as handle:
            for line in handle:
                if line.strip().startswith("GENLAYER_PRIVATE_KEY="):
                    value = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    if not value: raise SystemExit("GENLAYER_PRIVATE_KEY not found")
    return value if value.startswith("0x") else "0x" + value


def make_client():
    account = create_account(account_private_key=load_pk())
    return create_client(chain=studionet, account=account), account


def load_secondary_pk():
    value = os.environ.get("GENLAYER_SECONDARY_PRIVATE_KEY", "").strip()
    if not value:
        shared = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
        with open(shared, encoding="utf-8") as handle:
            for line in handle:
                if line.strip().startswith("GENLAYER_SECONDARY_PRIVATE_KEY="):
                    value = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    if not value: raise SystemExit("GENLAYER_SECONDARY_PRIVATE_KEY not found")
    return value if value.startswith("0x") else "0x" + value


def read_view(client, account, address, function_name, args=None):
    from genlayer_py.abi import calldata
    from genlayer_py.abi.transactions import serialize
    from genlayer_py.contracts.utils import make_calldata_object
    import eth_utils
    data = [calldata.encode(make_calldata_object(method=function_name,args=args or [],kwargs=None)), b"\x00"]
    result = client.provider.make_request(method="gen_call", params=[{"type":"read","to":address,"from":account.address,"data":serialize(data),"transaction_hash_variant":"latest-nonfinal"}])["result"]
    raw = result["data"] if isinstance(result,dict) else result
    return calldata.decode(eth_utils.hexadecimal.decode_hex("0x" + raw))
