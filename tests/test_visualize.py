from pathlib import Path
from llm_verification.visualize import plot_from_jsonl


def test_plot_from_sample(tmp_path):
    outdir = tmp_path / 'out'
    fixture = Path(__file__).parent / 'fixtures' / 'sample_outputs.jsonl'
    plot_from_jsonl(str(fixture), out_dir=str(outdir))
    assert (outdir / 'benford.png').exists()
    assert (outdir / 'zipf.png').exists()
