from llm_verification.analyzer_benford import extract_numbers_from_text, first_digits, benford_chi_squared


def test_benford_small():
    s = "Values: 10, 20, 30, 400, 5000"
    nums = extract_numbers_from_text(s)
    fd = first_digits(nums)
    chi2, p, counts, expected = benford_chi_squared(fd)
    assert counts.sum() == 5
    assert len(counts) == 9

