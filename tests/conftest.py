import os
import sys

# Ensure the project root is on sys.path so pytest can import the package
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import json
from pathlib import Path
import pytest

from llm_verification import utils


@pytest.fixture
def parsed_from_fixture():
    """Factory fixture: given a relative fixture path (str or Path),
    read the JSONL and return a list of parsed records:
    [{"id": ..., "model": ..., "numbers": [...], "cleaned": "..."}, ...]
    """

    def _factory(fixture_path):
        p = Path(fixture_path)
        if not p.exists():
            # try relative to tests/fixtures
            p = Path(__file__).parent / 'fixtures' / fixture_path
        data = utils.read_jsonl(str(p))
        out = []
        for rec in data:
            resp = rec.get('response', '')
            numbers, cleaned = utils.split_response_to_numbers_and_text(resp)
            out.append({
                'id': rec.get('id'),
                'model': rec.get('model'),
                'numbers': numbers,
                'cleaned': cleaned,
            })
        return out

    return _factory
