import datetime
import pytest
from moneyterm.utils.financedb import FinanceDB
from moneyterm.utils.ledger import Ledger
from moneyterm.utils import data_importer
from pathlib import Path
from collections import namedtuple
from moneyterm.utils.ledger import Transaction

DBTransaction = namedtuple("DBTransaction", ["date", "id", "memo", "payee", "type", "amount", "number"])
Account = namedtuple("Account", ["number", "account_type", "institution"])
Institution = namedtuple("Institution", ["organization"])
TEST_DIR = Path("tests")


@pytest.fixture(scope="session")
def di():
    return data_importer.load_ofx_data


@pytest.fixture(scope="session")
def dbtransaction():
    tx = DBTransaction(
        "2023-01-09 12:00:00",
        "8008",
        "Test Transaction Fixture",
        "TEST PAYEE",
        "POS",
        87.21,
        "1234",
    )
    return tx


@pytest.fixture(scope="function")
def transaction() -> Transaction:
    date_object = datetime.datetime.strptime("2023-01-09 12:00:00", "%Y-%m-%d %H:%M:%S")
    tx = Transaction(
        9999,
        date_object,
        "8008",
        "Test Transaction Fixture",
        "TEST PAYEE",
        "POS",
        87.21,
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
def db(ofx_parsed) -> FinanceDB:
    db_path = Path(TEST_DIR / "testdb.sqlite")
    db_path.unlink(missing_ok=True)
    db = FinanceDB(db_path=db_path)
    for ofx_data in ofx_parsed:
        db.import_ofx_data(ofx_data)
    return db


@pytest.fixture(scope="session")
def ledger(db) -> Ledger:
    testdb = db
    testledger = Ledger(testdb)
    return testledger


@pytest.fixture(scope="function", autouse=True)
def cleanup(db, ledger):
    yield
    db._execute_query("DELETE FROM transactions WHERE txid = '8008';")
    db._execute_query("DELETE FROM accounts WHERE number = '1234';")
    db._execute_query("DELETE FROM tags;")
    db._execute_query("DELETE FROM categories;")
    if "8008" in ledger.transactions:
        ledger.transactions.pop("8008")
    ledger.message_log.clear()
