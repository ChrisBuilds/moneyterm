from moneyterm.utils.ledger import Ledger
from pathlib import Path


def test_read_transactions_pkl_not_exist(ledger: Ledger):
    pkl_path = Path("nofile")
    assert ledger.read_ledger_pkl(pkl_path) == "not found"


def test_read_transactions_pkl_success(ledger: Ledger):
    pkl_path = Path("tests/test_data/ledger.pkl")
    assert ledger.read_ledger_pkl(pkl_path) == "success"


def test_import_transaction_data(ledger: Ledger):
    ledger = ledger
    ledger.load_ofx_data(Path("tests/test_data/test1.QFX"))
    ledger.load_ofx_data(Path("tests/test_data/test2.QFX"))
    ledger.load_ofx_data(Path("tests/test_data/test3.QFX"))
    assert len(ledger.accounts) == 3 and len(ledger.transactions) == 300


def test_load_transactions_pkl(ledger: Ledger):
    ledger.read_ledger_pkl(Path("tests/test_data/ledger.pkl"))
    assert len(ledger.accounts) == 3 and len(ledger.transactions) == 300
