from genlayer_py.types import transactions as _transactions


class _Activated:
    value = "ACTIVATED"


def apply():
    mapping = _transactions.TRANSACTION_STATUS_NUMBER_TO_NAME
    if "14" not in mapping: mapping["14"] = _Activated()
    if 14 not in mapping: mapping[14] = _Activated()
