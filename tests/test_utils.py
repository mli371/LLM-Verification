import pytest
from llm_verification.utils import split_response_to_numbers_and_text


def test_currency_and_thousands_separator():
    s = "Total: $1,234.56 was charged."
    nums, txt = split_response_to_numbers_and_text(s)
    assert len(nums) == 1
    assert abs(nums[0] - 1234.56) < 1e-6
    assert '1,234.56' not in txt


def test_negative_and_parentheses():
    s = "Adjustment: -42 and (1,000) recorded."
    nums, txt = split_response_to_numbers_and_text(s)
    assert -42.0 in nums
    assert -1000.0 in nums


def test_date_time_removed_and_clean_text():
    s = "On 2025-09-23 at 12:34:56 the value 3.14 was noted. Serial ABC-12345-678"
    nums, txt = split_response_to_numbers_and_text(s)
    assert 3.14 in nums
    assert '2025-09-23' not in txt
    assert '12:34:56' not in txt
    assert 'ABC-12345-678' not in txt
