from pathlib import Path
from ofxparse import ofxparse  # type: ignore
import pytest


def test_load_ofx_data_no_file(di):
    with pytest.raises(FileNotFoundError):
        ofx_data = di(Path("nofile"))


def test_load_ofx_data(di):
    ofx_file = Path("tests") / Path("test_data/test1.QFX")
    ofx_data = di(ofx_file)
    assert isinstance(ofx_data, ofxparse.Ofx)
    assert len(ofx_data.accounts) == 1
