from pathlib import Path
from ofxparse import ofxparse  # type: ignore


def test_load_ofx_data_no_file(di):
    ofx_data = di(Path("nofile"))
    assert ofx_data is None


def test_load_ofx_data(di):
    ofx_file = Path("tests") / Path("test1.QFX")
    ofx_data = di(ofx_file)
    assert isinstance(ofx_data, ofxparse.Ofx)
    assert len(ofx_data.accounts) == 1
