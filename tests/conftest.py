import datetime
import pytest
from moneyterm.utils.financedb import FinanceDB
from moneyterm.utils.ledger import Ledger
from moneyterm.utils import data_importer
from pathlib import Path
from decimal import Decimal
from collections import namedtuple
from moneyterm.utils.ledger import Transaction

# DBTransaction = namedtuple("DBTransaction", ["date", "id", "memo", "payee", "type", "amount", "number"])
Account = namedtuple("Account", ["number", "account_type", "institution"])
Institution = namedtuple("Institution", ["organization"])
TEST_DIR = Path("tests")


@pytest.fixture(scope="session")
def di():
    return data_importer.load_ofx_data


@pytest.fixture(scope="function")
def transaction() -> Transaction:
    date_object = datetime.datetime.strptime("2023-01-09 12:00:00", "%Y-%m-%d %H:%M:%S")
    tx = Transaction(
        date_object,
        "8008",
        "Test Transaction Fixture",
        "TEST PAYEE",
        "POS",
        Decimal("87.21"),
        "1234",
        list(),
        list(),
    )
    return tx


@pytest.fixture(scope="function")
def account():
    inst = Institution("TSTBNK")
    account = Account("1234", "TESTACCOUNT", inst)
    return account


@pytest.fixture(scope="session")
def ofx_parsed():
    parsed = []
    ofx_paths = (Path("test_data/test1.QFX"), Path("test_data/test2.QFX"), Path("test_data/test3.QFX"))
    for ofx_path in ofx_paths:
        parsed.append(data_importer.load_ofx_data(TEST_DIR / ofx_path))
    return parsed


@pytest.fixture(scope="session")
def ledger() -> Ledger:
    testledger = Ledger()
    return testledger


# @pytest.fixture(scope="function", autouse=True)
# def cleanup(db, ledger):
#     yield
#     db._execute_query("DELETE FROM transactions WHERE txid = '8008';")
#     db._execute_query("DELETE FROM accounts WHERE number = '1234';")
#     db._execute_query("DELETE FROM tags;")
#     db._execute_query("DELETE FROM expenses;")
#     if "8008" in ledger.transactions:
#         ledger.transactions.pop("8008")
#     ledger.message_log.clear()
