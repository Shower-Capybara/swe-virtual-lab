import pytest

from server.authentication.utils import process_header


@pytest.mark.parametrize("token", ["", "Bearer", "Basic 1"])
def test_process_header_invalid_token(token: str):
    with pytest.raises(Exception):
        process_header(token)


def test_process_header_valid_token():
    assert process_header("Bearer 1") == ("Bearer", "1")
