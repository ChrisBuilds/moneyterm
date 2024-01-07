"""
This module, ledger.py, provides classes for managing financial transactions and accounts.

Classes:
    Account: Represents a financial account with attributes such as number, account type, institution, and an optional alias.

    Labels: Manages lists of bill labels, category labels, and income labels.

    Transaction: Represents a financial transaction with attributes such as date, transaction ID, memo, payee, transaction type, amount, account number, labels, and tags.

    Ledger: Manages accounts and transactions. It provides methods to read the accounts and transactions from a pickle file.

This module also imports and uses several external libraries such as datetime, dataclasses, pickle, ofxparse, and others for various functionalities.

The module is part of a larger system for managing financial data and should be used in conjunction with other modules in the system.
"""

from datetime import datetime
from dataclasses import dataclass, field
import pickle
from ofxparse import Account as ofx_account  # type: ignore
from ofxparse import Transaction as ofx_transaction  # type: ignore
from moneyterm.utils import data_importer
from collections import defaultdict
from pathlib import Path
from decimal import Decimal


@dataclass(kw_only=True)
class Account:
    """
    Represents a financial account.

    Attributes:
        number (str): The account number.
        account_type (str): The type of account.
        institution (str): The financial institution associated with the account.
        alias (str, optional): An optional alias for the account.
    """

    number: str
    account_type: str
    institution: str
    alias: str = ""


@dataclass
class Labels:
    """
    A class representing labels used in a ledger.

    Attributes:
        bills (list[str]): List of bill labels.
        categories (list[str]): List of category labels.
        incomes (list[str]): List of income labels.
    """

    bills: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    incomes: list[str] = field(default_factory=list)


@dataclass(kw_only=True)
class Transaction:
    """
    Represents a financial transaction.

    Attributes:
        date (datetime): The date of the transaction.
        txid (str): The transaction ID.
        memo (str): A description or note about the transaction.
        payee (str): The payee or recipient of the transaction.
        tx_type (str): The type of transaction.
        amount (Decimal): The amount of the transaction.
        account_number (str): The account number associated with the transaction.
        auto_labels (Labels): The labels associated with the transaction.
        tags (list[str]): Additional tags for the transaction.
    """

    date: datetime
    txid: str
    memo: str
    payee: str
    tx_type: str
    amount: Decimal
    account: Account
    auto_labels: Labels
    manual_labels: Labels
    alias: str = ""


class Ledger:
    def __init__(self) -> None:
        self.accounts: dict[str, Account] = dict()
        self.transactions: dict[tuple[str, str], Transaction] = dict()
        self.pickle_path = Path("moneyterm/data/ledger.pkl")

    def read_ledger_pkl(self) -> str:
        """Read the accounts and transactions dicts from a pickle file.

        Args:
            pkl_file (Path): Path to the pickle file.

        Returns:
            str: "success", "failure" or "not found"
        """
        if not self.pickle_path.exists():
            return "not found"
        try:
            with open(self.pickle_path, "rb") as f:
                self.accounts, self.transactions = pickle.load(f)
            return "success"
        except:
            return "failure"

    def save_ledger_pkl(self) -> str:
        """Save the accounts and transactions dicts to a pickle file.

        Args:
            pkl_file (Path): Path to the pickle file.

        Returns:
            str: "success" or "failure"
        """
        try:
            with open(self.pickle_path, "wb") as f:
                pickle.dump((self.accounts, self.transactions), f)
            return "success"
        except:
            raise

    def load_ofx_data(self, data_file: Path) -> dict[str, int]:
        """Load OFX data from a file.

        Args:
            data_file (Path): Path to the OFX file.
        """
        load_results = {"accounts_added": 0, "transactions_added": 0, "transactions_ignored": 0}
        if not data_file.exists():
            return load_results
        ofx_data = data_importer.load_ofx_data(data_file)
        account: ofx_account
        tx: ofx_transaction
        for account in ofx_data.accounts:
            if account.number not in self.accounts:
                self.accounts[account.number] = Account(
                    number=account.number, account_type=account.type, institution=account.institution.organization
                )
                load_results["accounts_added"] += 1
            for tx in account.statement.transactions:
                if (account.number, tx.id) not in self.transactions:
                    self.transactions[(account.number, tx.id)] = Transaction(
                        date=tx.date.date(),
                        txid=tx.id,
                        memo=tx.memo,
                        payee=tx.payee,
                        tx_type=tx.type,
                        amount=tx.amount,
                        account=self.accounts[account.number],
                        auto_labels=Labels(),
                        manual_labels=Labels(),
                    )
                    load_results["transactions_added"] += 1
                else:
                    load_results["transactions_ignored"] += 1
        self.save_ledger_pkl()
        return load_results

    def find_dates_with_tx_activity(self, account_number: str | None = None) -> defaultdict[int, set[tuple[int, str]]]:
        """Find all dates with transaction activity.

        Args:
            account_number (str | None, optional): Account to read. If no account is provided, all accounts are read. Defaults to None.

        Returns:
            defaultdict[int, set[tuple[int, str]]]: Dictionary of years with a set of months with activity. E.g. {2021: {(1, "January"), (2, "February")}}
        """
        dates = defaultdict(set)
        for tx in self.transactions.values():
            if account_number is None or tx.account.number == account_number:
                dates[tx.date.year].add((tx.date.month, tx.date.strftime("%B")))
        return dates

    def get_tx_by_txid(self, account_number: str, txid: str) -> Transaction:
        """Get a transaction by its ID.

        Args:
            txid (str): Transaction ID

        Raises:
            ValueError: If the transaction is not found.

        Returns:
            Transaction: The transaction
        """
        transaction = self.transactions.get((account_number, txid))
        if transaction is None:
            raise ValueError(f"Transaction ({account_number}, {txid}) not found.")
        return transaction

    def get_all_tx(self) -> list[Transaction]:
        """Get all transactions.

        Returns:
            list[Transaction]: List of transactions
        """
        return sorted(self.transactions.values(), key=lambda tx: tx.date)

    def get_tx_by_account(self, account_number: str) -> list[Transaction]:
        """Get all transactions for an account.

        Args:
            account_number (str): Account number

        Returns:
            list[Transaction]: List of transactions
        """
        tx_list = [tx for tx in self.transactions.values() if tx.account.number == account_number]
        return sorted(tx_list, key=lambda tx: tx.date)

    def get_tx_by_year(self, account_number: str, year: int) -> list[Transaction]:
        """Get all transactions for a given year.

        Args:
            account_number (str): Account number
            year (int): Year

        Returns:
            list[Transaction]: List of transactions
        """
        tx_list = [
            tx for tx in self.transactions.values() if tx.account.number == account_number and tx.date.year == year
        ]
        return sorted(tx_list, key=lambda tx: tx.date)

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
            raise ValueError(f"Invalid month: {month}")
        tx_list = [
            tx
            for tx in self.transactions.values()
            if tx.account.number == account_number and tx.date.month == month and tx.date.year == year
        ]
        return sorted(tx_list, key=lambda tx: tx.date)

    def add_label_to_tx(self, account_number: str, txid: str, label_str: str, label_type: str, auto=True) -> None:
        """Add a label to a transaction.

        Args:
            txid (str): Transaction ID
            label_str (str): Label to add
            label_type (str): Type of label to add
            auto (bool, optional): Whether the label is automatically generated. Defaults to True.
        """
        if label_type == "bills":
            auto_labels = self.transactions[(account_number, txid)].auto_labels.bills
            manual_labels = self.transactions[(account_number, txid)].manual_labels.bills
        elif label_type == "categories":
            auto_labels = self.transactions[(account_number, txid)].auto_labels.categories
            manual_labels = self.transactions[(account_number, txid)].manual_labels.categories
        elif label_type == "incomes":
            auto_labels = self.transactions[(account_number, txid)].auto_labels.incomes
            manual_labels = self.transactions[(account_number, txid)].manual_labels.incomes

        if label_str not in auto_labels and label_str not in manual_labels:
            if auto:
                auto_labels.append(label_str)
                auto_labels.sort()
            else:
                manual_labels.append(label_str)
                manual_labels.sort()

    def remove_label_from_tx(self, account_number: str, txid: str, label_str: str) -> None:
        transaction = self.get_tx_by_txid(account_number, txid)
        for label_list in (
            transaction.manual_labels.bills,
            transaction.manual_labels.categories,
            transaction.manual_labels.incomes,
        ):
            if label_str in label_list:
                label_list.remove(label_str)
                label_list.sort()

    def remove_label(self, label: str) -> None:
        """Removes a label from all transactions manual_labels. Labels in auto_labels will be automatically
        updated on the next call to Labeler.scan_and_update_transactions().

        Args:
            label (str): Label to remove
        """
        for tx in self.get_all_tx():
            for label_list in (tx.manual_labels.bills, tx.manual_labels.categories, tx.manual_labels.incomes):
                if label in label_list:
                    label_list.remove(label)
                    label_list.sort()

    def rename_label(self, old_label: str, new_label: str) -> None:
        """Renames labels in the manual_labels labels. Labels in auto_labels will be automatically
        updated on the next call to Labeler.scan_and_update_transactions().

        Args:
            old_label (str): Old label
            new_label (str): New label
        """
        for tx in self.get_all_tx():
            for label_list in (tx.manual_labels.bills, tx.manual_labels.categories, tx.manual_labels.incomes):
                if old_label in label_list:
                    label_list.remove(old_label)
                    label_list.append(new_label)
                    label_list.sort()

    def get_all_tx_with_label(self, label: str) -> list[Transaction]:
        """Get all transactions with a given label.

        Args:
            label (str): Category to search for

        Returns:
            list[Transaction]: List of transactions with the given label
        """
        tx_with_label: list[Transaction] = []
        for tx in self.transactions.values():
            all_labels = (
                tx.auto_labels.bills
                + tx.auto_labels.categories
                + tx.auto_labels.incomes
                + tx.manual_labels.bills
                + tx.manual_labels.categories
                + tx.manual_labels.incomes
            )
            if label in all_labels:
                tx_with_label.append(tx)
        return tx_with_label

    def add_account_alias(self, account_number: str, alias: str) -> None:
        """Add an alias to an account.

        Args:
            account_number (str): Account number
            alias (str): Alias
        """
        if account_number in self.accounts:
            self.accounts[account_number].alias = alias
