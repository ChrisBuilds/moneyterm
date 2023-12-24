from datetime import datetime
from dataclasses import dataclass
import pickle
from ofxparse import Account as ofx_account  # type: ignore
from ofxparse import Transaction as ofx_transaction  # type: ignore
from moneyterm.utils import data_importer
from collections import defaultdict
from pathlib import Path
from decimal import Decimal

MAXTAGS = 5


@dataclass
class Account:
    number: str
    account_type: str
    institution: str


@dataclass
class Transaction:
    date: datetime
    txid: str
    memo: str
    payee: str
    tx_type: str
    amount: Decimal
    account_number: str
    categories: list[str]
    tags: list[str]


class Ledger:
    def __init__(self) -> None:
        self.accounts: dict[str, Account] = dict()
        self.transactions: dict[str, Transaction] = dict()

    def read_ledger_pkl(self, pkl_file: Path) -> str:
        """Read the accounts and transactions dicts from a pickle file.

        Args:
            pkl_file (Path): Path to the pickle file.

        Returns:
            str: "success", "failure" or "not found"
        """
        if not pkl_file.exists():
            return "not found"
        try:
            with open(pkl_file, "rb") as f:
                self.accounts, self.transactions = pickle.load(f)
            return "success"
        except:
            return "failure"

    def save_ledger_pkl(self, pkl_file: Path) -> str:
        """Save the accounts and transactions dicts to a pickle file.

        Args:
            pkl_file (Path): Path to the pickle file.

        Returns:
            str: "success" or "failure"
        """
        try:
            with open(pkl_file, "wb") as f:
                pickle.dump((self.accounts, self.transactions), f)
            return "success"
        except:
            return "failure"

    def load_ofx_data(self, data_file: Path) -> None:
        """Load OFX data from a file.

        Args:
            data_file (Path): Path to the OFX file.
        """
        if not data_file.exists():
            return
        ofx_data = data_importer.load_ofx_data(data_file)
        account: ofx_account
        tx: ofx_transaction
        transactions_added = 0
        accounts_added = 0
        for account in ofx_data.accounts:
            if account.number not in self.accounts:
                self.accounts[account.number] = Account(account.number, account.type, account.institution.organization)
                accounts_added += 1
            for tx in account.statement.transactions:
                if tx.id not in self.transactions:
                    self.transactions[tx.id] = Transaction(
                        tx.date, tx.id, tx.memo, tx.payee, tx.type, tx.amount, account.number, list(), list()
                    )
                    transactions_added += 1

    def find_dates_with_tx_activity(self, account_number: str | None = None) -> defaultdict[int, set[tuple[int, str]]]:
        """Find all dates with transaction activity.

        Args:
            account_number (str | None, optional): Account to read. If no account is provided, all accounts are read. Defaults to None.

        Returns:
            defaultdict[int, set[tuple[int, str]]]: Dictionary of years with a set of months with activity. E.g. {2021: {(1, "January"), (2, "February")}}
        """
        dates = defaultdict(set)
        for tx in self.transactions.values():
            if account_number is None or tx.account_number == account_number:
                dates[tx.date.year].add((tx.date.month, tx.date.strftime("%B")))
        return dates

    def get_tx_by_txid(self, txid: str) -> Transaction:
        """Get a transaction by its ID.

        Args:
            txid (str): Transaction ID

        Raises:
            ValueError: If the transaction is not found.

        Returns:
            Transaction: The transaction
        """
        transaction = self.transactions.get(txid)
        if transaction is None:
            raise ValueError(f"Transaction {txid} not found.")
        return transaction

    def get_tx_by_month(self, account_number: str, year: int, month: int) -> list[Transaction]:
        """Get all transactions for a given month.

        Args:
            account_number (str): Account number
            year (int): year
            month (int): month

        Returns:
            list[Transaction]: List of transactions
        """
        if month not in range(1, 13):
            return []
        tx_list = [
            tx
            for tx in self.transactions.values()
            if tx.account_number == account_number and tx.date.month == month and tx.date.year == year
        ]
        return sorted(tx_list, key=lambda tx: tx.date)

    def add_tag_to_tx(self, txid: str, tag_str: str) -> None:
        """Add a tag to a transaction.

        Args:
            txid (str): Transaction ID
            tag_str (str): Tag to add
        """
        if tag_str not in self.transactions[txid].tags:
            self.transactions[txid].tags.append(tag_str)

    def remove_tag_from_tx(self, txid: str, tag_str: str) -> None:
        """Remove a tag from a transaction.

        Args:
            txid (str): Transaction ID
            tag_str (str): Tag to remove
        """
        if tag_str in self.transactions[txid].tags:
            self.transactions[txid].tags.remove(tag_str)

    def add_category_to_tx(self, txid: str, category_str: str):
        """Add a category to a transaction.

        Args:
            txid (str): Transaction ID
            category_str (str): Category to add
        """
        if category_str not in self.transactions[txid].categories:
            self.transactions[txid].categories.append(category_str)

    def remove_category_from_tx(self, txid: str, category_str: str):
        """Remove a category from a transaction.

        Args:
            txid (str): Transaction ID
            category_str (str): Category to remove
        """
        if category_str in self.transactions[txid].categories:
            self.transactions[txid].categories.remove(category_str)

    def get_all_tx_with_category(self, category: str) -> list[Transaction]:
        """Get all transactions with a given category.

        Args:
            category (str): Category to search for

        Returns:
            list[Transaction]: List of transactions with the given category
        """
        tx_list = [tx for tx in self.transactions.values() if category in tx.categories]
        return tx_list
