from llm_verification.collector import collect_from_prompts_file, save_jsonl
from llm_verification.utils import read_jsonl


def test_collect_prompts(tmp_path):
    p = tmp_path / 'prompts.txt'
    p.write_text('# comment\nFirst prompt\nSecond prompt\n')
    prompts = collect_from_prompts_file(str(p))
    assert prompts == ['First prompt', 'Second prompt']


def test_save_and_read_jsonl(tmp_path):
    out = tmp_path / 'out.jsonl'
    records = [{"prompt": "a", "response": "b"}, {"prompt": "c", "response": "d"}]
    save_jsonl(str(out), records)
    read = list(read_jsonl(str(out)))
    assert read == records


def test_collect_parallel_dryrun():
    from llm_verification.collector import collect_openai_parallel
    prompts = ['p1', 'p2', 'p3']
    recs = collect_openai_parallel(prompts, dry_run=True, max_workers=3)
    assert len(recs) == 3
    assert all('prompt' in r and 'timestamp' in r for r in recs)
