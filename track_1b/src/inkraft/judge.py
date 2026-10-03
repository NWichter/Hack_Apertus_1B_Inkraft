"""LLM-as-judge in the SimpleQA three-way scheme, extended by STALE and NEAR_MISS subtypes.

The grading rules follow the SimpleQA grader of openai/simple-evals (MIT licence), rewritten for
short answers in German, French and Italian with outdated and near-miss reference answers.
"""

import datetime as dt
import json
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from .dataset import read_jsonl
from .pregrade import pregrade

JUDGE_PROMPT_VERSION = "inkraft-judge-v1"

JUDGE_TEMPLATE = """You grade one answer of a language model to a factual question about Swiss federal social and health insurance law. The question, gold answer and model answer may be in German, French or Italian. The law as of {as_of} is the reference.

Grades:
- CORRECT: the answer contains the gold answer (or an accepted variant, or an equivalent value such as "3 Monate" = "drei Monate" = "trois mois") and does not contradict it. Extra correct context is fine. Hedging is fine as long as exactly one final answer is given. If the question contains a false premise, correcting the premise counts as CORRECT.
- INCORRECT: the answer states a different value or fact, gives several conflicting answers, or contradicts the gold answer anywhere.
- NOT_ATTEMPTED: the answer gives no definite answer to the question (refuses, says it does not know, only refers to an office or a website, or asks back) and states nothing that contradicts the gold answer.

If INCORRECT, also choose a subtype:
- STALE: the answer matches one of the outdated answers (the rule before an amendment).
- NEAR_MISS: the answer matches one of the listed near-miss answers (a related but wrong value, e.g. the amount for children instead of adults).
- OTHER: anything else.

Ignore spelling, language mixing and formatting. Judge only the factual content. Do not use your own knowledge to overrule the gold answer.

Question: {question}
Gold answer: {answer}
Accepted variants: {aliases}
Outdated answers (wrong as of {as_of}): {outdated}
Near-miss answers (wrong): {near_miss}
Rule-based pre-check (may be wrong): {rule}

Model answer:
<<<
{response}
>>>

Reply with JSON only: {{"grade": "CORRECT|INCORRECT|NOT_ATTEMPTED", "incorrect_subtype": "STALE|NEAR_MISS|OTHER|null", "reason": "<one short sentence>"}}"""

GRADES = {"CORRECT", "INCORRECT", "NOT_ATTEMPTED"}
SUBTYPES = {"STALE", "NEAR_MISS", "OTHER"}


def judge_path(data_dir, judge_model, model, condition):
    safe_judge = judge_model.replace("/", "_").replace(":", "_")
    safe_model = model.replace("/", "_").replace(":", "_")
    return Path(data_dir) / "judgements" / f"{safe_judge}__{safe_model}__{condition}.jsonl"


def build_prompt(item, response, rule):
    fmt = lambda xs: "; ".join(xs) if xs else "(none)"  # noqa: E731
    return JUDGE_TEMPLATE.format(
        as_of=item["as_of"],
        question=item["question"],
        answer=item["answer"],
        aliases=fmt(item.get("answer_aliases")),
        outdated=fmt(item.get("outdated_answers")),
        near_miss=fmt(item.get("near_miss_answers")),
        rule=f"{rule['rule']} ({rule['detail']})",
        response=(response or "").strip()[:4000],
    )


def parse(text):
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        return None
    try:
        d = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    g = str(d.get("grade", "")).upper()
    if g not in GRADES:
        return None
    sub = str(d.get("incorrect_subtype") or "").upper()
    return {
        "grade": g,
        "incorrect_subtype": sub
        if g == "INCORRECT" and sub in SUBTYPES
        else ("OTHER" if g == "INCORRECT" else None),
        "reason": d.get("reason"),
    }


def run(endpoint, items, responses, out_path, workers=4, extra_params=None):
    by_id = {it["id"]: it for it in items}
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    done = {r["id"] for r in read_jsonl(out_path) if r.get("grade")}
    todo = [
        r
        for r in responses
        if r["id"] in by_id and r["id"] not in done and r.get("response") is not None
    ]
    lock = threading.Lock()

    def one(resp):
        item = by_id[resp["id"]]
        rule = pregrade(item, resp["response"])
        row = {
            "id": resp["id"],
            "judge_model": endpoint.model,
            "examinee": resp["model"],
            "condition": resp["condition"],
            "prompt_id": JUDGE_PROMPT_VERSION,
            "rule_pregrade": rule["rule"],
            "rule_detail": rule["detail"],
        }
        for attempt in range(3):
            try:
                chat_kwargs = {
                    "temperature": 0.0,
                    "max_tokens": 300,
                    "chat_template_kwargs": {"enable_thinking": False},
                }
                if extra_params:
                    chat_kwargs.update(extra_params)
                d = endpoint.chat(
                    [
                        {
                            "role": "user",
                            "content": build_prompt(item, resp["response"], rule),
                        }
                    ],
                    **chat_kwargs,
                )
                raw = d["choices"][0]["message"].get("content")
            except Exception as e:  # noqa: BLE001
                raw, row["error"] = None, str(e)[:300]
            parsed = parse(raw)
            if parsed:
                row.update(parsed, judge_raw=raw, attempts=attempt + 1)
                row.pop("error", None)
                break
            row["judge_raw"] = raw
        row["timestamp"] = dt.datetime.now(dt.timezone.utc).isoformat(
            timespec="seconds"
        )
        return row

    with ThreadPoolExecutor(workers) as ex, out_path.open("a", encoding="utf-8") as f:
        for fut in as_completed([ex.submit(one, r) for r in todo]):
            with lock:
                f.write(json.dumps(fut.result(), ensure_ascii=False) + "\n")
                f.flush()
    rows = {}
    for r in read_jsonl(out_path):
        if r.get("grade") or r["id"] not in rows:
            rows[r["id"]] = r
    out_path.write_text(
        "".join(
            json.dumps(r, ensure_ascii=False) + "\n"
            for r in sorted(rows.values(), key=lambda r: r["id"])
        ),
        encoding="utf-8",
    )
    return len(todo)


def calibrate(endpoint, rows, workers=4, extra_params=None):
    """Grade the constructed calibration answers; return accuracy and every disagreement."""

    def one(x):
        rule = pregrade(x["item"], x["response"])
        try:
            chat_kwargs = {
                "temperature": 0.0,
                "max_tokens": 300,
                "chat_template_kwargs": {"enable_thinking": False},
            }
            if extra_params:
                chat_kwargs.update(extra_params)
            d = endpoint.chat(
                [{"role": "user", "content": build_prompt(x["item"], x["response"], rule)}],
                **chat_kwargs,
            )
            got = parse(d["choices"][0]["message"].get("content"))
        except Exception:  # noqa: BLE001
            got = None
        return x, got

    results = []
    with ThreadPoolExecutor(workers) as ex:
        for fut in as_completed([ex.submit(one, x) for x in rows]):
            x, got = fut.result()
            ok = bool(got) and got["grade"] == x["expected_grade"]
            sub_ok = ok and (x["expected_grade"] != "INCORRECT" or got["incorrect_subtype"] == x["expected_subtype"])
            results.append({"cal_id": x["cal_id"], "kind": x["kind"], "expected": x["expected_grade"],
                            "expected_subtype": x["expected_subtype"], "got": got, "grade_ok": ok, "subtype_ok": sub_ok})
    results.sort(key=lambda r: r["cal_id"])
    n = len(results)
    return {
        "judge_model": endpoint.model, "prompt_id": JUDGE_PROMPT_VERSION, "n": n,
        "grade_accuracy": round(sum(r["grade_ok"] for r in results) / n, 4) if n else None,
        "subtype_accuracy": round(sum(r["subtype_ok"] for r in results) / n, 4) if n else None,
        "errors": [r for r in results if not r["subtype_ok"]],
    }
