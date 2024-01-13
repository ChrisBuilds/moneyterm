import sqlite3
from pathlib import Path
from ofxparse import Account, Transaction  # type: ignore

DB_PATH = Path("moneyterm/data/real.sqlite")

ACCOUNT_ROW = tuple[int, str, str, str]
TRANSACTION_ROW = tuple[
    int,
    str,
    str,
    str,
    str,
    str,
    float,
    int,
    str | None,
    str | None,
    str | None,
    str | None,
    str | None,
    str | None,
    str | None,
    str | None,
    str | None,
    str | None,
]


class FinanceDB:
    """Manage the sqlite database containing finance data."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.connection = self.create_connection()
        self.create_tables()

    def create_connection(self) -> sqlite3.Connection:
        """Connect to the sqlite database."""
        connection = None
        if not self.db_path.exists():
            # implement logging
            # print(f"Database at location: {self.db_path} not found!!!")
            ...
        try:
            connection = sqlite3.connect(self.db_path)
            connection.execute("PRAGMA foreign_keys = on")
        except sqlite3.Error as e:
            raise e
        return connection

    def _execute_query(self, query: str) -> None:
        """Execute queries on the sqlite database."""
        cursor = self.connection.cursor()
        try:
            cursor.execute(query)
            self.connection.commit()
        except sqlite3.Error as e:
            raise e

    def _execute_read_query(self, query) -> list:
        cursor = self.connection.cursor()
        result = []
        try:
            cursor.execute(query)
            result = cursor.fetchall()
        except sqlite3.Error as e:
            raise e
        return result

    def insert_tx(self, account_number: str, tx: Transaction) -> None:
        """Insert a transaction into the transaction table."""

        insert_statement = f"""
        INSERT INTO transactions 
            (date, txid, memo, payee, type, amount, account_number)
        VALUES 
        ("{str(tx.date)}", "{tx.id}", "{tx.memo}", "{tx.payee}", "{tx.type}", {float(tx.amount)}, "{account_number}"); 
        """
        self._execute_query(insert_statement)

    def delete_tx(self, txid: str) -> None:
        """Delete a transaction from the transactions table."""
        delete_statement = f"""
        DELETE FROM transactions WHERE txid = '{txid}';
        """
        self._execute_query(delete_statement)

    def query_transactions(self, transaction_id: str | None = None) -> list[TRANSACTION_ROW]:
        """Query database for transaction by transaction id, or all if no id is given."""
        if not transaction_id:
            transaction_query = f"""
            SELECT * FROM transactions;
            """
        else:
            transaction_query = f"""
            SELECT * FROM transactions WHERE txid = '{transaction_id}';
            """
        transactions = self._execute_read_query(transaction_query)
        return transactions

    def insert_account(self, account: Account) -> None:
        """Insert an account into the accounts table."""
        insert_statement = f"""
        INSERT INTO accounts
            (number, type, institution)
        VALUES
            ("{account.number}", "{account.account_type}", "{account.institution.organization}");
        """
        self._execute_query(insert_statement)

    def delete_account(self, account: Account) -> None:
        """Delete an account from the accounts table."""
        delete_statement = f"""
        DELETE FROM accounts WHERE number = '{account.number}';
        """
        self._execute_query(delete_statement)

    def query_accounts(self, account_number: str | None = None) -> list[ACCOUNT_ROW]:
        """Query database for account by account number, or all if no number is given."""
        if not account_number:
            account_query = f"""
            SELECT * FROM accounts;
            """
            accounts = self._execute_read_query(account_query)
        else:
            account_query = f"""
            SELECT * FROM accounts WHERE number = {account_number};
            """
            accounts = self._execute_read_query(account_query)
        return accounts

    def query_expenses(self, expense_id: int | None = None) -> list[tuple[int, str]]:
        """Query database for expense by expense id, or all if no id is given."""
        if not expense_id:
            expense_query = f"""
            SELECT * FROM expenses;
            """
        else:
            expense_query = f"""
            SELECT * FROM expenses WHERE id = {expense_id};
            """
        expenses = self._execute_read_query(expense_query)
        return expenses

    def insert_expense(self, expense_str: str) -> None:
        """Insert a expense into the database if not already present."""
        expenses = [expense[1] for expense in self.query_expenses()]
        if expense_str not in expenses:
            insert_statement = f"""
            INSERT INTO expenses
                (expense)
            VALUES
                ("{expense_str}");
            """
            self._execute_query(insert_statement)

    def delete_expense(self, expense_str: str | None = None, expense_id: int | None = None) -> None:
        """Delete a expense from the database."""
        if not expense_str and not expense_id:
            raise ValueError("finanacedb.delete_expense: Must provide either expense string or expense id.")
        delete_statement = f"""
        DELETE FROM expenses WHERE {'expense' if expense_str else 'id'} = '{expense_str if expense_str else expense_id}';
        """
        self._execute_query(delete_statement)

    def query_tags(self, tag_id: int | None = None) -> list[tuple[int, str]]:
        """Query database for tag by tag id, or all if no id is given."""
        if not tag_id:
            tag_query = f"""
            SELECT * FROM tags;
            """
        else:
            tag_query = f"""
            SELECT * FROM tags WHERE id = {tag_id};
            """
        tags = self._execute_read_query(tag_query)
        return tags

    def insert_tag(self, tag_str: str) -> None:
        """Insert a tag if it is not already present in the database."""
        tags = [tag[1] for tag in self.query_tags()]
        if tag_str not in tags:
            insert_statement = f"""
            INSERT INTO tags
                (tag)
            VALUES
                ("{tag_str}");
            """
            self._execute_query(insert_statement)

    def delete_tag(self, tag_str: str) -> None:
        """Delete a tag from the database."""
        delete_statement = f"""
        DELETE FROM tags WHERE tag = '{tag_str}';
        """
        self._execute_query(delete_statement)

    def add_tag_to_tx(self, transaction_id: str, tag_str: str) -> None:
        """Add tag to transaction if transaction has available tag slot and tag not already present."""
        tx = self.query_transactions(transaction_id)[0]
        current_tags = tx[13:]
        if tag_str in current_tags:
            return
        for slot, tag in enumerate(tx[13:18]):
            if tag is None:
                insert_statement = f"""
                UPDATE transactions
                SET tag{slot} = '{tag_str}'
                WHERE txid = '{transaction_id}';
                """
                self._execute_query(insert_statement)
                return

    def remove_tag_from_tx(self, transaction_id: str, tag_str: str) -> None:
        """Remove a tag from a transaction."""
        tx = self.query_transactions(transaction_id)[0]
        current_tags = tx[13:]
        tag_slot = current_tags.index(tag_str)
        update_statement = f"""
        UPDATE transactions
        SET tag{tag_slot} = NULL
        WHERE txid = '{transaction_id}';
        """
        self._execute_query(update_statement)

    def add_expense_to_tx(self, transaction_id: str, expense_str: str) -> None:
        """Add expense to transaction if transaction has available expense slot and expense not already present."""
        tx = self.query_transactions(transaction_id)[0]
        current_expenses = tx[8:13]
        if expense_str in current_expenses:
            return
        for slot, expense in enumerate(current_expenses):
            if expense is None:
                insert_statement = f"""
                UPDATE transactions
                SET expense{slot} = '{expense_str}'
                WHERE txid = '{transaction_id}';
                """
                self._execute_query(insert_statement)
                return

    def remove_expense_from_tx(self, transaction_id: str, expense_str: str) -> None:
        """Remove a tag from a transaction."""
        tx = self.query_transactions(transaction_id)[0]
        current_expenses = tx[8:13]
        expense_slot = current_expenses.index(expense_str)
        update_statement = f"""
        UPDATE transactions
        SET expense{expense_slot} = NULL
        WHERE txid = '{transaction_id}';
        """
        self._execute_query(update_statement)

    def create_tables(self) -> None:
        """Create any table that doesn't exist."""
        create_accounts_table = """
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                number TEXT UNIQUE,
                type TEXT,
                institution TEXT
            );
        """
        create_transactions_table = """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                txid TEXT,
                memo TEXT,
                payee TEXT,
                type TEXT,
                amount REAL,
                account_number INT,
                expense0 STR,
                expense1 STR,                
                expense2 STR,
                expense3 STR,
                expense4 STR,
                tag0 STR,
                tag1 STR,
                tag2 STR,
                tag3 STR,
                tag4 STR,
                FOREIGN KEY (account_number) REFERENCES accounts (number),
                FOREIGN KEY (expense0) REFERENCES expenses (expense),                
                FOREIGN KEY (expense1) REFERENCES expenses (expense),
                FOREIGN KEY (expense2) REFERENCES expenses (expense),
                FOREIGN KEY (expense3) REFERENCES expenses (expense),
                FOREIGN KEY (expense4) REFERENCES expenses (expense),
                FOREIGN KEY (tag0) REFERENCES tags (tag)   
                FOREIGN KEY (tag1) REFERENCES tags (tag),
                FOREIGN KEY (tag2) REFERENCES tags (tag),
                FOREIGN KEY (tag3) REFERENCES tags (tag),
                FOREIGN KEY (tag4) REFERENCES tags (tag)
            );
        """
        create_expenses_table = """
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                expense TEXT UNIQUE
            );
            
                """
        create_tags_table = """
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tag TEXT UNIQUE
            );
    """
        self._execute_query(create_accounts_table)
        self._execute_query(create_expenses_table)
        self._execute_query(create_tags_table)
        self._execute_query(create_transactions_table)

    def import_ofx_data(self, ofx_data) -> None:
        account: Account
        tx: Transaction
        transactions_added = 0
        accounts_added = 0
        for account in ofx_data.accounts:
            if not self.query_accounts(account.number):
                self.insert_account(account)
                accounts_added += 1
            for tx in account.statement.transactions:
                if not self.query_transactions(tx.id):
                    self.insert_tx(account.number, tx)
                    transactions_added += 1

    def query_transactions_with_expense(self, expense: str) -> list[TRANSACTION_ROW]:
        """Query database for transactions with a given expense."""
        query = f"""
        SELECT * FROM transactions WHERE expense0 = '{expense}' OR expense1 = '{expense}' OR expense2 = '{expense}' OR expense3 = '{expense}' OR expense4 = '{expense}';
        """
        transactions = self._execute_read_query(query)
        return transactions


if __name__ == "__main__":
    db = FinanceDB()
    ...
