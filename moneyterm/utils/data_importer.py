import ofxparse
from pathlib import Path


def load_ofx_data(ofx_path: Path) -> ofxparse.ofxparse.Ofx:
    """Load OFX data from a file.

    Args:
        ofx_path (Path): Path to the OFX file.

    Raises:
        FileNotFoundError: If the OFX file does not exist.

    Returns:
        ofxparse.ofxparse.Ofx: The parsed OFX data.
    """
    if not ofx_path.exists():
        raise FileNotFoundError(f"OFX file {ofx_path} does not exist.")
    with open(ofx_path) as f:
        parsed_ofx_data = ofxparse.OfxParser.parse(f, fail_fast=True)
    return parsed_ofx_data
