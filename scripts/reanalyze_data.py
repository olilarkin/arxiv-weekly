#!/usr/bin/env python3
"""
reanalyze_data.py
Force-overwrite the AI-generated fields in existing weekly JSONs using the
current analyze_papers prompt.
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

import yaml
from openai import OpenAI

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from analyze_papers import (
    SYSTEM_PROMPT,
    DailyQuotaExceededError,
    analyze_batch,
    build_next_reads,
    chunk_papers,
    fallback_result,
)

FAILED_MARKER = "Analysis failed."

SETTINGS = yaml.safe_load((ROOT / "config/settings.yaml").read_text())
WEEKLY_DIR = ROOT / "data" / "weekly"

AI_FIELDS = ("org", "task", "proposedMethod", "datasets",
             "what", "novel", "method", "validation", "discussion",
             "nextReads")


def get_client() -> OpenAI:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise EnvironmentError("GITHUB_TOKEN is not set")
    cfg = SETTINGS["github_models"]
    return OpenAI(base_url=cfg["endpoint"], api_key=token)


def reanalyze_file(path: Path, client: OpenAI, ai_results: dict) -> bool:
    data = json.loads(path.read_text())
    changed = False

    for cat in data.get("categories", []):
        for paper in cat.get("papers", []):
            arxiv_id = paper["id"].split("v")[0]
            if arxiv_id not in ai_results:
                continue

            result = ai_results[arxiv_id]
            for field in ("org", "task", "proposedMethod",
                          "datasets", "what", "novel", "method",
                          "validation", "discussion"):
                new_val = result.get(field)
                if new_val is not None and new_val != "":
                    if paper.get(field) != new_val:
                        paper[field] = new_val
                        changed = True

            new_reads = build_next_reads(result.get("nextReads", []))
            if new_reads and paper.get("nextReads") != new_reads:
                paper["nextReads"] = new_reads
                changed = True

    if changed:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        print(f"[reanalyze] Saved -> {path.name}")
    else:
        print(f"[reanalyze] No changes -> {path.name}")

    return changed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--only-failed",
        action="store_true",
        help="Only re-analyze papers whose 'what' field is the fallback 'Analysis failed.' marker.",
    )
    args = parser.parse_args()

    client = get_client()
    cfg = SETTINGS["github_models"]

    # Collect papers across all weekly files.
    all_papers = []
    skipped_ok = 0
    for path in sorted(WEEKLY_DIR.glob("*.json")):
        data = json.loads(path.read_text())
        for cat in data.get("categories", []):
            for paper in cat.get("papers", []):
                if not paper.get("abstract"):
                    continue
                if args.only_failed and paper.get("what") != FAILED_MARKER:
                    skipped_ok += 1
                    continue
                all_papers.append(paper)

    mode = "only-failed" if args.only_failed else "all"
    print(f"[reanalyze] Mode: {mode}")
    if args.only_failed:
        print(f"[reanalyze] Skipping {skipped_ok} already-analyzed papers")
    print(f"[reanalyze] Target papers: {len(all_papers)}")
    print(f"[reanalyze] Batch size: {cfg['batch_size']} -> ~{-(-len(all_papers) // cfg['batch_size'])} API calls")

    if not all_papers:
        print("[reanalyze] Nothing to do.")
        return

    # Regenerate AI fields in batches.
    ai_results: dict[str, dict] = {}
    batches = chunk_papers(all_papers, cfg["batch_size"])
    last_request_at = None
    quota_hit = False

    for i, batch in enumerate(batches, 1):
        ids = [p["id"].split("v")[0] for p in batch]
        print(f"[reanalyze] batch ({i}/{len(batches)}) ids={', '.join(ids)}")
        try:
            batch_results, last_request_at = analyze_batch(client, batch, last_request_at)
        except DailyQuotaExceededError as e:
            # Apply whatever we have so far, then stop.
            print(f"\n[reanalyze] GitHub Models daily quota exhausted at batch {i}/{len(batches)} — applying partial results.")
            print(f"[reanalyze] Reason: {e}")
            quota_hit = True
            break

        for paper in batch:
            arxiv_id = paper["id"].split("v")[0]
            result = batch_results.get(paper["id"], fallback_result(paper))
            ai_results[arxiv_id] = result

    print(f"\n[reanalyze] AI analysis complete: {len(ai_results)} papers")

    # Update each file (uses ai_results map; files without affected papers are no-ops).
    for path in sorted(WEEKLY_DIR.glob("*.json")):
        print(f"\n[reanalyze] --- {path.name} ---")
        reanalyze_file(path, client, ai_results)

    print("\n[reanalyze] Done." + (" (partial — re-run after quota refresh)" if quota_hit else ""))


if __name__ == "__main__":
    main()
