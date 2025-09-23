from llm_verification.analyzer_zipf import zipf_stats


def test_zipf_small():
    texts = ["apple banana apple orange banana apple"]
    ranks, freqs, slope = zipf_stats(texts)
    assert len(freqs) == 3
    assert slope < 0
