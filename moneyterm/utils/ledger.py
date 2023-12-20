from datetime import datetime
from dataclasses import dataclass
from moneyterm.utils.financedb import FinanceDB
from moneyterm.utils import data_importer
from collections import defaultdict
from pathlib import Path

MAXTAGS = 5


@dataclass
class Account:
    dbid: int
    number: str
    account_type: str
    institution: str


@dataclass
class Transaction:
    dbid: int
    date: datetime
    txid: str
    memo: str
    payee: str
    tx_type: str
    amount: float
    account_number: str
    categories: list[str]
    tags: list[str]


class Ledger:
    def __init__(self, db: FinanceDB):
        self.db = db
        self.accounts: dict[str, Account] = dict()
        self.transactions: dict[str, Transaction] = dict()
        self.load_db()
        self.message_log: list[str] = []

    def find_dates_with_tx_activity(self, account_number: str | None = None) -> defaultdict[int, set[tuple[int, str]]]:
        """
        Return dict of year : (month, month_name) pairs for all months with transaction data for the given account. If
        not account is given, all transactions are considered.
        Returns:
            defaultdict[int, set[tuple[int, str]]]: dict of year : (month, month_name) pairs
        """
        dates = defaultdict(set)
        for tx in self.transactions.values():
            if account_number is None or tx.account_number == account_number:
                dates[tx.date.year].add((tx.date.month, tx.date.strftime("%B")))
        return dates

    def get_tx_by_txid(self, txid: str) -> Transaction:
        transaction = self.transactions.get(txid)
        if transaction is None:
            self.message_log.append(f"Transaction {txid} not found.")
            raise ValueError(f"Transaction {txid} not found.")
        return transaction

    def get_tx_by_month(self, account_number: str, year: int, month: int) -> list[Transaction]:
        """Get all transactions from a given month and year."""
        if month not in range(1, 13):
            return []
        tx_list = [
            tx
            for tx in self.transactions.values()
            if tx.account_number == account_number and tx.date.month == month and tx.date.year == year
        ]
        return sorted(tx_list, key=lambda tx: tx.date)

    def load_db(self) -> None:
        """Load database accounts, transactions, categories, and tags into the ledger."""
        accounts_rows = self.db.query_accounts()
        for account_row in accounts_rows:
            account = Account(*account_row)
            self.accounts[account.number] = account

        for transaction_row in self.db.query_transactions():
            transaction = self._make_tx_from_row(transaction_row)
            self.transactions[transaction.txid] = transaction

    def import_transaction_data(self, data_file: Path) -> None:
        if not data_file.exists():
            return
        ofx_data = data_importer.load_ofx_data(data_file)
        self.db.import_ofx_data(ofx_data)
        self.load_db()

    @staticmethod
    def _make_tx_from_row(tx_row) -> Transaction:
        """Parse a row from the transactions table into a Transaction object."""
        dbid = tx_row[0]
        date = datetime.strptime(tx_row[1], "%Y-%m-%d %H:%M:%S")
        txid = tx_row[2]
        memo = tx_row[3]
        payee = tx_row[4]
        tx_type = tx_row[5]
        amount = tx_row[6]
        account_number = str(tx_row[7])
        categories = []
        categories.extend([cat for cat in tx_row[8:13] if cat])
        tags = []
        tags.extend([tag for tag in tx_row[13:] if tag])
        transaction = Transaction(
            dbid,
            date,
            txid,
            memo,
            payee,
            tx_type,
            amount,
            account_number,
            categories,
            tags,
        )
        return transaction

    def _update_tx_from_db(self, txid: str) -> None:
        transaction = self._make_tx_from_row(self.db.query_transactions(txid)[0])
        self.transactions[txid] = transaction

    def get_all_tags(self) -> list[str]:
        """Get a list of all tags in the database, sorted alphabetically."""
        tags = self.db.query_tags()
        tag_list = []
        if tags:
            tag_list = sorted([tag[1] for tag in tags])
        return tag_list

    def add_tag(self, tag_str: str) -> None:
        self.db.insert_tag(tag_str)

    def delete_tag(self, tag_str: str) -> None:
        if any([tag_str in tx.tags for tx in self.transactions.values()]):
            message = f"Cannot delete tag: {tag_str}. There are transactions assigned this tag."
            self.message_log.append(message)
        else:
            self.db.delete_tag(tag_str)

    def add_tag_to_tx(self, transaction: Transaction, tag_str: str) -> None:
        if len(transaction.tags) == MAXTAGS:
            self.message_log.append(f"Cannot add tag: {tag_str} to transaction. Transaction has {MAXTAGS} (max) tags.")
        else:
            self.db.add_tag_to_tx(transaction.txid, tag_str)
            self._update_tx_from_db(transaction.txid)

    def remove_tag_from_tx(self, transaction: Transaction, tag_str: str) -> None:
        if tag_str in transaction.tags:
            self.db.remove_tag_from_tx(transaction.txid, tag_str)
            self._update_tx_from_db(transaction.txid)

    def get_all_categories(self) -> dict[int, str]:
        categories = self.db.query_categories()
        categories_dict = {cat[0]: cat[1] for cat in categories}
        return categories_dict

    def add_category(self, category_str: str) -> None:
        self.db.insert_category(category_str)

    def delete_category(self, category_str: str) -> None:
        if any([category_str in tx.categories for tx in self.transactions.values()]):
            message = f"Cannot delete category: {category_str}. There are transactions assigned this category."
            self.message_log.append(message)
        else:
            self.db.delete_category(category_str)

    def add_category_to_tx(self, transaction: Transaction, category_str: str) -> None:
        if len(transaction.categories) == 5:
            self.message_log.append(
                f"Cannot add category: {category_str} to transaction. Transaction has 5 (max) categories."
            )
        else:
            self.db.add_category_to_tx(transaction.txid, category_str)
            self._update_tx_from_db(transaction.txid)

    def remove_cateogry_from_tx(self, transaction: Transaction, category_str: str) -> None:
        self.db.remove_category_from_tx(transaction.txid, category_str)
        self._update_tx_from_db(transaction.txid)
