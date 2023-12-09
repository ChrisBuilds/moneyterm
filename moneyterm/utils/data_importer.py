import ofxparse
from ofxparse import OfxParser
from pathlib import Path


def load_ofx_data(ofx_path: Path) -> ofxparse.ofxparse.Ofx | None:
    """Parse an OFX file."""
    if not ofx_path.exists():
        return None
    with open(ofx_path) as f:
        return OfxParser.parse(f, fail_fast=True)
