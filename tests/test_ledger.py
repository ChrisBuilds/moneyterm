import pytest


def test_read_db(ledger):
    assert len(ledger.accounts) == 3 and len(ledger.transactions) == 300


def test_ledger_parse_transaction(db, ledger, account, dbtransaction):
    db.insert_account(account)
    db.insert_tx(account.number, dbtransaction)
    ledger._update_tx_from_db("8008")
    assert ledger.transactions["8008"].memo == "Test Transaction Fixture"
    assert ledger.transactions["8008"].amount == 87.21


def test_get_all_tags(ledger, db):
    db.insert_tag("test_tag0")
    db.insert_tag("test_tag1")
    tags = ledger.get_all_tags()
    assert "test_tag0" in tags and "test_tag1" in tags


def test_add_tag(ledger):
    ledger.add_tag("test_tag0")
    tags = ledger.get_all_tags()
    assert "test_tag0" in tags


def test_cannot_add_duplicate_tags(ledger):
    ledger.add_tag("test_tag0")
    ledger.add_tag("test_tag0")
    tags = ledger.get_all_tags()
    assert len(tags) == 1


def test_delete_tag(ledger):
    ledger.add_tag("test_tag0")
    ledger.delete_tag("test_tag0")
    tags = ledger.get_all_tags()
    assert "test_tag0" not in tags


def test_cannot_delete_tag_in_use(db, ledger, account, dbtransaction):
    db.insert_account(account)
    db.insert_tx(account.number, dbtransaction)
    ledger._update_tx_from_db("8008")
    ledger.add_tag("test_tag0")
    ledger.add_tag_to_tx(ledger.transactions["8008"], "test_tag0")
    ledger.delete_tag("test_tag0")
    assert len(ledger.message_log) == 1 and "assigned this tag" in ledger.message_log[0]


def test_add_tag_to_tx(db, ledger, account, dbtransaction):
    db.insert_account(account)
    db.insert_tx(account.number, dbtransaction)
    ledger._update_tx_from_db("8008")
    ledger.add_tag("test_tag0")
    ledger.add_tag_to_tx(ledger.transactions["8008"], "test_tag0")
    assert "test_tag0" in ledger.transactions["8008"].tags


def test_cannot_add_more_than_five_tags_to_tx(db, ledger, account, dbtransaction):
    db.insert_account(account)
    db.insert_tx(account.number, dbtransaction)
    ledger._update_tx_from_db("8008")
    for i in range(6):
        tag_str = f"test_tag{i}"
        ledger.add_tag(tag_str)
        ledger.add_tag_to_tx(ledger.transactions["8008"], tag_str)
    assert len(ledger.message_log) == 1 and "(max) tags" in ledger.message_log[0]


def test_cannot_add_tag_that_does_not_exist_to_tx(db, ledger, account, dbtransaction):
    db.insert_account(account)
    db.insert_tx(account.number, dbtransaction)
    ledger._update_tx_from_db("8008")
    with pytest.raises(Exception):
        ledger.add_tag_to_tx(ledger.transactions["8008"], "test_tag0")


def test_remove_tag_from_tx(db, ledger, account, dbtransaction):
    db.insert_account(account)
    db.insert_tx(account.number, dbtransaction)
    ledger._update_tx_from_db("8008")
    ledger.add_tag("test_tag0")
    ledger.add_tag_to_tx(ledger.transactions["8008"], "test_tag0")
    ledger.remove_tag_from_tx(ledger.transactions["8008"], "test_tag0")
    assert "test_tag0" not in ledger.transactions["8008"].tags


def test_add_category(ledger):
    category_str = "test_category0"
    ledger.add_category(category_str)
    categories = ledger.get_all_categories()
    assert category_str in categories.values()


def test_get_all_categories(ledger):
    categories = ["test_category0", "test_category1"]
    for cat in categories:
        ledger.add_category(cat)
    db_categories = ledger.get_all_categories()
    assert all([cat in db_categories.values() for cat in categories])


def test_delete_category(ledger):
    category_str = "test_category0"
    ledger.add_category(category_str)
    ledger.delete_category(category_str)
    assert category_str not in ledger.get_all_categories().values()


def test_cannot_delete_category_in_use(db, ledger, account, dbtransaction):
    db.insert_account(account)
    db.insert_tx(account.number, dbtransaction)
    ledger._update_tx_from_db("8008")
    category_str = "test_category0"
    ledger.add_category(category_str)
    ledger.add_category_to_tx(ledger.transactions["8008"], category_str)
    ledger.delete_category(category_str)
    assert (
        len(ledger.message_log) == 1
        and "assigned this category" in ledger.message_log[0]
    )


def test_add_category_to_tx(db, ledger, account, dbtransaction):
    db.insert_account(account)
    db.insert_tx(account.number, dbtransaction)
    ledger._update_tx_from_db("8008")
    category_str = "test_category0"
    ledger.add_category(category_str)
    ledger.add_category_to_tx(ledger.transactions["8008"], category_str)
    assert category_str in ledger.transactions["8008"].categories


def test_cannot_add_more_than_five_categories_to_tx(db, ledger, account, dbtransaction):
    db.insert_account(account)
    db.insert_tx(account.number, dbtransaction)
    ledger._update_tx_from_db("8008")
    for i in range(6):
        category_str = f"test_category{i}"
        ledger.add_category(category_str)
        ledger.add_category_to_tx(ledger.transactions["8008"], category_str)
    assert len(ledger.message_log) == 1 and "(max) categories" in ledger.message_log[0]


def test_remove_category_from_tx(db, ledger, account, dbtransaction):
    db.insert_account(account)
    db.insert_tx(account.number, dbtransaction)
    ledger._update_tx_from_db("8008")
    category_str = "test_category0"
    ledger.add_category(category_str)
    ledger.add_category_to_tx(ledger.transactions["8008"], category_str)
    ledger.remove_cateogry_from_tx(ledger.transactions["8008"], category_str)
    assert category_str not in ledger.transactions["8008"].categories
