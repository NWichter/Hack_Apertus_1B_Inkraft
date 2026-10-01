"""Query the examinee for every item and condition. Resumable: finished ids are skipped."""

import datetime as dt
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from .dataset import read_jsonl
from .prompts import PROMPT_VERSION, extra_params, messages, split_reasoning

PARAMS = {"temperature": 0.0, "top_p": 1.0, "max_tokens": 256, "seed": 20261001}


def response_path(data_dir, model, condition):
    return Path(data_dir) / "responses" / f"{model}__{condition}.jsonl"


def run(endpoint, items, condition, out_path, workers=8, max_tokens=None):
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    done = {r["id"] for r in read_jsonl(out_path) if r.get("response") is not None}
    todo = [it for it in items if it["id"] not in done]
    params = {**PARAMS, **extra_params(condition), **({"max_tokens": max_tokens} if max_tokens else {})}
    lock = threading.Lock()

    def one(it):
        msgs = messages(it, condition)
        row = {
            "id": it["id"],
            "model": endpoint.model,
            "endpoint": endpoint.host,
            "condition": condition,
            "prompt_version": PROMPT_VERSION,
            "params": params,
            "messages": msgs,
        }
        try:
            d = endpoint.chat(msgs, **params)
            ch = d["choices"][0]
            msg = ch["message"]
            answer, reasoning = split_reasoning(msg.get("content"))
            row.update(
                response=answer if answer is not None else "",
                reasoning=reasoning or msg.get("reasoning_content") or msg.get("reasoning"),
                finish_reason=ch.get("finish_reason"),
                model_revision=d.get("model"),
                tokens_in=(d.get("usage") or {}).get("prompt_tokens"),
                tokens_out=(d.get("usage") or {}).get("completion_tokens"),
                latency_ms=d.get("_latency_ms"),
            )
        except Exception as e:  # noqa: BLE001 - keep the run going, record the failure
            row.update(response=None, error=str(e)[:500])
        row["timestamp"] = dt.datetime.now(dt.timezone.utc).isoformat(
            timespec="seconds"
        )
        return row

    n_err = 0
    with ThreadPoolExecutor(workers) as ex, out_path.open("a", encoding="utf-8") as f:
        for fut in as_completed([ex.submit(one, it) for it in todo]):
            row = fut.result()
            n_err += row.get("response") is None
            with lock:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
                f.flush()
    _dedupe(out_path)
    return len(todo), n_err


def _dedupe(path):
    """Keep the last successful row per id (retries append)."""
    rows = {}
    for r in read_jsonl(path):
        if r.get("response") is not None or r["id"] not in rows:
            rows[r["id"]] = r
    Path(path).write_text(
        "".join(
            json.dumps(r, ensure_ascii=False) + "\n"
            for r in sorted(rows.values(), key=lambda r: r["id"])
        ),
        encoding="utf-8",
    )
