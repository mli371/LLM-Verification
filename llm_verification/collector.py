import os
import json
import time
from typing import List, Iterable, Dict
from .utils import read_jsonl
from concurrent.futures import ThreadPoolExecutor, as_completed


def load_from_jsonl(path: str) -> List[dict]:
    return list(read_jsonl(path))


def save_jsonl(path: str, records: Iterable[Dict]):
    """Append records to a JSONL file."""
    with open(path, 'a', encoding='utf-8') as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')


def collect_openai(prompts: List[str], model: str = 'gpt-4o', api_key_env: str = 'OPENAI_API_KEY',
                   max_retries: int = 3, sleep_between: float = 1.0, dry_run: bool = False) -> List[dict]:
    """Collect responses from OpenAI (or dry-run returning prompts only).

    Returns a list of records: {prompt, response, model, timestamp, error?}
    """
    if dry_run:
        return [{"prompt": p, "response": None, "model": model, "timestamp": time.time()} for p in prompts]

    try:
        # new OpenAI python client exposes OpenAI class
        from openai import OpenAI
    except Exception:
        raise RuntimeError('openai package not available in environment; install it to enable API collection')

    # Try to load .env if present (makes local testing easier)
    try:
        from dotenv import load_dotenv
        # Prefer values in project .env over existing environment variables
        load_dotenv(override=True)
    except Exception:
        pass

    key = os.getenv(api_key_env)
    if not key:
        raise RuntimeError(f'Please set environment variable {api_key_env}')
    # instantiate client (it will also read from env if supported)
    client = OpenAI(api_key=key)
    outputs: List[dict] = []
    for p in prompts:
        attempt = 0
        while True:
            attempt += 1
            try:
                # new API: client.chat.completions.create
                resp = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": p}],
                )
                # response structure remains similar: choices -> message -> content
                text = resp.choices[0].message.content
                # treat empty or whitespace-only responses as transient failures to allow retries
                if not text or not str(text).strip():
                    raise RuntimeError('empty response')
                rec = {"prompt": p, "response": text, "model": model, "timestamp": time.time()}
                outputs.append(rec)
                break
            except Exception as e:
                if attempt >= max_retries:
                    outputs.append({
                        "prompt": p,
                        "response": None,
                        "model": model,
                        "timestamp": time.time(),
                        "error": str(e),
                    })
                    break
                # small backoff before retrying
                time.sleep(sleep_between)
    return outputs


def collect_from_prompts_file(prompts_path: str) -> List[str]:
    with open(prompts_path, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
    return lines


def _collect_single(client, prompt: str, model: str) -> dict:
    # helper for parallel execution; client is an OpenAI() instance exposing chat.completions.create
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        text = resp.choices[0].message.content
        if not text or not str(text).strip():
            return {
                "prompt": prompt,
                "response": None,
                "model": model,
                "timestamp": time.time(),
                "error": "empty response",
            }
        return {
            "prompt": prompt,
            "response": text,
            "model": model,
            "timestamp": time.time(),
        }
    except Exception as e:
        return {"prompt": prompt, "response": None, "model": model, "timestamp": time.time(), "error": str(e)}


def collect_openai_parallel(prompts: List[str], model: str = 'gpt-4o', api_key_env: str = 'OPENAI_API_KEY',
                            max_workers: int = 4, dry_run: bool = False) -> List[dict]:
    """Collect using a ThreadPoolExecutor. For dry_run, returns records quickly without network calls."""
    if dry_run:
        return [{"prompt": p, "response": None, "model": model, "timestamp": time.time()} for p in prompts]

    try:
        from openai import OpenAI
    except Exception:
        raise RuntimeError('openai package not available in environment; install it to enable API collection')

    # Try to load .env if present
    try:
        from dotenv import load_dotenv
        # Prefer values in project .env over existing environment variables
        load_dotenv(override=True)
    except Exception:
        pass

    key = os.getenv(api_key_env)
    if not key:
        raise RuntimeError(f'Please set environment variable {api_key_env}')
    client = OpenAI(api_key=key)

    results: List[dict] = []
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {
            ex.submit(_collect_single, client, p, model): p
            for p in prompts
        }
        for fut in as_completed(futures):
            results.append(fut.result())
    return results


