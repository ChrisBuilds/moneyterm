import pytest


def test_query_accounts_valid_account(db):
    assert len(db.query_accounts()) == 3


def test_query_accounts_invalid_account(db):
    assert len(db.query_accounts(account_number="0")) == 0


def test_insert_account(db, account):
    db.insert_account(account)
    result = db.query_accounts(account.number)
    assert len(result) == 1


def test_delete_account(db, account):
    db.insert_account(account)
    db.delete_account(account)
    result = db.query_accounts(account.number)
    assert len(result) == 0


def test_insert_tx_valid_account(db, dbtransaction, account):
    db.insert_account(account)
    account_number = dbtransaction.number
    db.insert_tx(account_number, dbtransaction)
    tx = db.query_transactions("8008")
    assert len(tx) == 1


def test_insert_tx_invalid_account(db, dbtransaction):
    account_number = "1111"
    with pytest.raises(Exception):
        db.insert_tx(account_number, dbtransaction)


def test_insert_new_tag(db):
    db.insert_tag("test_tag")
    tags = [tag[1] for tag in db.query_tags()]
    assert "test_tag" in tags


def test_query_tag(db):
    db.insert_tag("test_tag")
    tagid, tag = db.query_tags()[0]
    results = db.query_tags(tagid)[0]
    assert results == (tagid, tag)


def test_insert_tag_already_exists(db):
    db.insert_tag("test_tag")
    db.insert_tag("test_tag")
    tags = [tag[1] for tag in db.query_tags()]
    assert tags.count("test_tag") == 1


def test_delete_tag_from_db(db):
    db.insert_tag("test_tag")
    db.insert_tag("delete_tag")
    db.delete_tag(tag_str="delete_tag")
    tags = [tag[1] for tag in db.query_tags()]
    assert "delete_tag" not in tags


def test_insert_new_category(db):
    db.insert_category("test_category")
    categories = [category[1] for category in db.query_categories()]
    assert "test_category" in categories


def test_query_category(db):
    db.insert_category("test_category")
    catid, cat = db.query_categories()[0]
    results = db.query_categories(catid)[0]
    assert results == (catid, cat)


def test_insert_category_already_exists(db):
    db.insert_category("test_category")
    db.insert_category("test_category")
    categories = [category[1] for category in db.query_categories()]
    assert categories.count("test_category") == 1


def test_delete_category_from_db(db):
    db.insert_category("test_category")
    db.insert_category("delete_category")
    db.delete_category(category_str="delete_category")
    categories = [category[1] for category in db.query_categories()]
    assert "delete_category" not in categories


def test_add_tag_to_tx(db, dbtransaction, account):
    db.insert_account(account)
    db.insert_tx(account.number, dbtransaction)
    db.insert_tag("test_tag")
    db.add_tag_to_tx(dbtransaction.id, "test_tag")
    tx = db.query_transactions(dbtransaction.id)[0]
    tags = tx[13:]
    assert "test_tag" in tags


def test_add_multiple_tags_to_tx(db, account, dbtransaction):
    db.insert_account(account)
    db.insert_tx(account.number, dbtransaction)
    db.insert_tag("test_tag0")
    db.insert_tag("test_tag1")
    db.insert_tag("test_tag2")
    db.insert_tag("test_tag3")
    db.insert_tag("test_tag4")
    db.add_tag_to_tx(dbtransaction.id, "test_tag0")
    db.add_tag_to_tx(dbtransaction.id, "test_tag1")
    db.add_tag_to_tx(dbtransaction.id, "test_tag2")
    db.add_tag_to_tx(dbtransaction.id, "test_tag3")
    db.add_tag_to_tx(dbtransaction.id, "test_tag4")
    tx = db.query_transactions(dbtransaction.id)[0]
    tags = tx[13:]
    assert len(tags) == 5


def test_delete_tag_from_tx(db, account, dbtransaction):
    db.insert_account(account)
    db.insert_tx(account.number, dbtransaction)
    db.insert_tag("test_tag1")
    db.add_tag_to_tx(dbtransaction.id, "test_tag1")
    db.remove_tag_from_tx(dbtransaction.id, "test_tag1")
    tx = db.query_transactions(dbtransaction.id)[0]
    tags = tx[13:]
    assert not any(tags)


def test_add_category_to_tx(db, account, dbtransaction):
    db.insert_account(account)
    db.insert_tx(account.number, dbtransaction)
    db.insert_category("test_category")
    db.add_category_to_tx(dbtransaction.id, "test_category")
    tx = db.query_transactions(dbtransaction.id)[0]
    categories = tx[8:13]
    assert "test_category" in categories


def test_add_multiple_categories_to_tx(db, account, dbtransaction):
    db.insert_account(account)
    db.insert_tx(account.number, dbtransaction)
    db.insert_category("test_category0")
    db.insert_category("test_category1")
    db.insert_category("test_category2")
    db.insert_category("test_category3")
    db.insert_category("test_category4")
    db.add_category_to_tx(dbtransaction.id, "test_category0")
    db.add_category_to_tx(dbtransaction.id, "test_category1")
    db.add_category_to_tx(dbtransaction.id, "test_category2")
    db.add_category_to_tx(dbtransaction.id, "test_category3")
    db.add_category_to_tx(dbtransaction.id, "test_category4")
    tx = db.query_transactions(dbtransaction.id)[0]
    categories = tx[8:13]
    assert len(categories) == 5


def test_delete_category_from_tx(db, account, dbtransaction):
    db.insert_account(account)
    db.insert_tx(account.number, dbtransaction)
    db.insert_category("test_category")
    db.add_category_to_tx(dbtransaction.id, "test_category")
    db.remove_category_from_tx(dbtransaction.id, "test_category")
    tx = db.query_transactions(dbtransaction.id)[0]
    categories = tx[8:13]
    assert not any(categories)
