#!/usr/bin/env python3
"""
analyze_papers.py
Analyze each paper from six angles using GitHub Models (GPT-4o).
"""

import json
import os
import time
from pathlib import Path

import yaml
from openai import APIError, OpenAI

from model_utils import build_chat_kwargs

ROOT = Path(__file__).parent.parent
SETTINGS = yaml.safe_load((ROOT / "config/settings.yaml").read_text())
KEYWORDS = yaml.safe_load((ROOT / "config/keywords.yaml").read_text())

SYSTEM_PROMPT = """You are a research analyst for the audio and acoustics AI field.
Analyze the given paper (title and abstract) and reply ONLY with JSON in the
exact schema below. Do not include any preamble, explanation, or code-fence
markers (such as ```json).

## Terminology guidance

Distinguish these terms carefully:
- Speech: human spoken language.
- Sound / Acoustic: physical sound in general, including instruments and environmental sound.
- Audio: sound as an electrical signal or data.
- Voice: biological voice, including singing.

Use precise English terminology in all fields, e.g.:
- "audio source separation" (not "speech separation") when instruments or noise are involved.
- "acoustic event detection" (not "speech event detection").
- "speech enhancement", "voice activity detection", "sound localization", etc.

## Output schema

{
  "org": "Primary author affiliation (short, e.g. MIT / Google)",
  "task": "Task category (e.g. TTS / ASR / Source Separation / Anomalous Sound Detection / Music Generation), 1-3 words",
  "proposedMethod": "Name or acronym of the proposed method (e.g. SALMONN, AudioSep). Use null if none.",
  "datasets": ["Dataset name 1", "Dataset name 2"],
  "what": "What it is (1-2 sentences summarizing the paper)",
  "novel": "What is novel compared to prior work (1-2 sentences)",
  "method": "Core technical idea / architecture / training trick (1-2 sentences)",
  "validation": "How it is validated: datasets, metrics, comparisons (1-2 sentences)",
  "discussion": "Discussion and limitations: open issues, constraints (1-2 sentences)",
  "nextReads": [
    {"label": "Related paper title (year)", "id": "arXiv ID (e.g. 2310.13289) or null"}
  ]
}

nextReads should contain 3-4 entries. Use null for the arXiv ID when unknown.
datasets should list up to 5 datasets used for training or evaluation.
All values must be in English."""


def get_client() -> OpenAI:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise EnvironmentError("GITHUB_TOKEN is not set")
    cfg = SETTINGS["github_models"]
    return OpenAI(base_url=cfg["endpoint"], api_key=token)


def sanitize_json_text(raw: str) -> str:
    return raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()


def wait_for_next_request(last_request_at: float | None, min_interval: float):
    if last_request_at is None:
        return
    elapsed = time.monotonic() - last_request_at
    remaining = min_interval - elapsed
    if remaining > 0:
        print(f"[analyze] waiting {remaining:.1f}s to respect model rate limit ...")
        time.sleep(remaining)


def build_batch_prompt(papers: list[dict]) -> str:
    paper_blocks = []
    for paper in papers:
        paper_blocks.append(
            f"""ID: {paper["id"]}
Title: {paper["title"]}
Authors: {", ".join(paper.get("authors", [])[:3])}
Categories: {", ".join(paper.get("categories", []))}
Date: {paper.get("date", "")}

Abstract:
{paper["abstract"]}"""
        )

    joined = "\n\n---\n\n".join(paper_blocks)
    return f"""Analyze the papers below. Return ONE JSON object whose keys are
the paper IDs and whose values follow this schema:

{{
  "<paper_id>": {{
    "org": "Primary author affiliation (short, e.g. MIT / Google)",
    "task": "Task category (e.g. TTS / ASR / Source Separation / Anomalous Sound Detection), 1-3 words",
    "proposedMethod": "Name or acronym of the proposed method (null if none)",
    "datasets": ["Dataset name 1", "Dataset name 2"],
    "what": "What it is (1-2 sentences)",
    "novel": "Novelty vs prior work (1-2 sentences)",
    "method": "Core technical idea (1-2 sentences)",
    "validation": "Datasets / metrics / comparisons (1-2 sentences)",
    "discussion": "Discussion and limitations (1-2 sentences)",
    "nextReads": [
      {{"label": "Related paper title (year)", "id": "arXiv ID or null"}}
    ]
  }}
}}

Provide 3-4 nextReads entries per paper; use null for unknown arXiv IDs.
List up to 5 datasets used for training or evaluation.
All values must be in English.

{joined}"""


def fallback_result(paper: dict) -> dict:
    return {
        "org": paper.get("org", ""),
        "task": None,
        "proposedMethod": None,
        "datasets": [],
        "what": "Analysis failed.",
        "novel": "",
        "method": "",
        "validation": "",
        "discussion": "",
        "nextReads": [],
    }


def analyze_batch(
    client: OpenAI, papers: list[dict], last_request_at: float | None
) -> tuple[dict[str, dict], float | None]:
    cfg = SETTINGS["github_models"]
    prompt = build_batch_prompt(papers)
    paper_ids = {paper["id"] for paper in papers}

    for attempt in range(cfg["retry_max"]):
        request_started_at = None
        try:
            wait_for_next_request(last_request_at, cfg["min_request_interval"])
            request_started_at = time.monotonic()
            resp = client.chat.completions.create(
                model=cfg["model"],
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                **build_chat_kwargs(
                    cfg["model"], cfg["batch_max_tokens"], temperature=0.3
                ),
            )
            last_request_at = time.monotonic()
            raw = sanitize_json_text(resp.choices[0].message.content or "")
            result = json.loads(raw)
            if not isinstance(result, dict):
                raise json.JSONDecodeError(
                    "Batch response is not a JSON object", raw, 0
                )
            missing_ids = sorted(paper_ids - set(result.keys()))
            if missing_ids:
                raise json.JSONDecodeError(
                    f"Missing paper ids: {', '.join(missing_ids)}", raw, 0
                )
            return result, last_request_at
        except json.JSONDecodeError as e:
            if request_started_at is not None:
                last_request_at = request_started_at
            print(f"  [warn] JSON parse error (attempt {attempt + 1}): {e}")
        except APIError as e:
            if request_started_at is not None:
                last_request_at = request_started_at
            print(f"  [warn] API error (attempt {attempt + 1}): {e}")
        time.sleep(cfg["retry_interval"] * (2**attempt))

    return {paper["id"]: fallback_result(paper) for paper in papers}, last_request_at


def chunk_papers(papers: list[dict], batch_size: int) -> list[list[dict]]:
    return [
        papers[index : index + batch_size]
        for index in range(0, len(papers), batch_size)
    ]


def build_next_reads(items: list[dict]) -> list[dict]:
    result = []
    for item in items:
        arxiv_id = item.get("id")
        url = f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else None
        result.append({"label": item.get("label", ""), "url": url})
    return result


def main():
    raw_path = ROOT / "data" / "raw_papers.json"
    if not raw_path.exists():
        raise FileNotFoundError(
            f"{raw_path} not found. Run fetch_papers.py first."
        )

    papers = json.loads(raw_path.read_text())
    print(f"[analyze] Analyzing {len(papers)} papers ...")

    client = get_client()
    cfg = SETTINGS["github_models"]
    analyzed = []
    batches = chunk_papers(papers, cfg["batch_size"])
    last_request_at = None

    for batch_index, batch in enumerate(batches, 1):
        batch_ids = ", ".join(paper["id"] for paper in batch)
        print(
            f"[analyze] batch ({batch_index}/{len(batches)}) size={len(batch)} ids={batch_ids}"
        )
        batch_results, last_request_at = analyze_batch(client, batch, last_request_at)

        for paper in batch:
            result = batch_results.get(paper["id"], fallback_result(paper))
            analyzed.append(
                {
                    "id": paper["id"],
                    "date": paper["date"],
                    "title": paper["title"],
                    "authors": paper.get("authors", []),
                    "org": result.get("org") or paper.get("org", ""),
                    "abstract": paper.get("abstract", ""),
                    "comment": paper.get("comment"),
                    "journalRef": paper.get("journalRef"),
                    "categories": paper.get("categories", []),
                    "url": paper["url"],
                    "category": paper.get("category", "other"),
                    "task": result.get("task"),
                    "proposedMethod": result.get("proposedMethod"),
                    "datasets": result.get("datasets", []),
                    "what": result.get("what", ""),
                    "novel": result.get("novel", ""),
                    "method": result.get("method", ""),
                    "validation": result.get("validation", ""),
                    "discussion": result.get("discussion", ""),
                    "nextReads": build_next_reads(result.get("nextReads", [])),
                }
            )

    out_path = ROOT / "data" / "analyzed_papers.json"
    out_path.write_text(json.dumps(analyzed, ensure_ascii=False, indent=2))
    print(f"[analyze] Saved → {out_path}")


if __name__ == "__main__":
    main()
