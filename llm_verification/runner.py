"""Small CLI for batch collection of prompts to JSONL outputs."""
import argparse
from .collector import collect_openai, collect_openai_parallel, collect_from_prompts_file, save_jsonl


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--prompts', '-p', required=True, help='Path to prompts file (one prompt per line)')
    p.add_argument('--out', '-o', required=True, help='Output JSONL file')
    p.add_argument('--model', '-m', default='gpt-4o', help='Model name to query')
    p.add_argument('--topic', type=str, default='', help='Optional topic label to annotate each record as _topic')
    p.add_argument('--dry-run', action='store_true', help='Do not call API, just record prompts')
    p.add_argument('--workers', type=int, default=1, help='Number of worker threads for parallel collection')
    p.add_argument('--batch-size', type=int, default=0, help='If >0, split prompts into batches of this size')
    p.add_argument('--max-batches', type=int, default=0, help='If >0, stop after processing this many batches')
    p.add_argument('--max-prompts', type=int, default=0, help='If >0, stop after processing this many prompts in total')
    p.add_argument('--models', type=str, default='', help='Comma-separated list of models to query (overrides --model)')
    p.add_argument('--n-per-prompt', type=int, default=1, help='Number of samples to collect per prompt per model')
    args = p.parse_args()

    prompts = collect_from_prompts_file(args.prompts)
    model_list = [m.strip() for m in args.models.split(',') if m.strip()] if args.models else [args.model]

    def chunks(lst, n):
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

    total_written = 0
    processed_prompts = 0
    if args.batch_size and args.batch_size > 0:
        for i, batch in enumerate(chunks(prompts, args.batch_size), start=1):
            # enforce max-batches if set
            if args.max_batches and args.max_batches > 0 and i > args.max_batches:
                print(f'Reached max-batches limit ({args.max_batches}), stopping.')
                break
            # if max-prompts set, possibly trim the last batch so we don't exceed the limit
            if args.max_prompts and args.max_prompts > 0:
                remaining = args.max_prompts - processed_prompts
                if remaining <= 0:
                    print(f'Reached max-prompts limit ({args.max_prompts}), stopping.')
                    break
                if len(batch) > remaining:
                    batch = batch[:remaining]
            print(
                f"Processing batch {i} (size {len(batch)})..."
            )
            for model in model_list:
                for rep in range(args.n_per_prompt):
                    print(f"  model={model} rep={rep+1}/{args.n_per_prompt}")
                    if args.workers and args.workers > 1:
                        records = collect_openai_parallel(batch, model=model, max_workers=args.workers, dry_run=args.dry_run)
                    else:
                        records = collect_openai(batch, model=model, dry_run=args.dry_run)
                    # annotate topic if provided
                    if args.topic:
                        for r in records:
                            r["_topic"] = args.topic
                    save_jsonl(args.out, records)
                    total_written += len(records)
                    processed_prompts += len(batch)
                    print(f"  Appended {len(records)} records (total {total_written})")
    else:
        for model in model_list:
            for rep in range(args.n_per_prompt):
                print(f"Collecting for model={model} rep={rep+1}/{args.n_per_prompt}...")
                if args.workers and args.workers > 1:
                    records = collect_openai_parallel(prompts, model=model, max_workers=args.workers, dry_run=args.dry_run)
                else:
                    records = collect_openai(prompts, model=model, dry_run=args.dry_run)
                # annotate topic if provided
                if args.topic:
                    for r in records:
                        r["_topic"] = args.topic
                save_jsonl(args.out, records)
                total_written += len(records)
                print(f"Appended {len(records)} records (total {total_written})")


if __name__ == '__main__':
    main()
