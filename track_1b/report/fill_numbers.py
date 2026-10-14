"""Every number quoted in the report, the data card, the READMEs, the project page and the pitch, computed from the
stored files, and written into those documents between markers <!--n:KEY-->…<!--/n-->.

Numbers that depend on the human check show a neutral "pending" text (the marker "[[NIKLAS-PRÜFUNG: KEY]]" stays as an
HTML comment) until data/human_labels/summary.json exists. Sentences that only make sense with or without the human check
sit in <!--when:human-->…<!--/when:human--> / <!--when:pending-->…<!--/when:pending--> blocks (also hf / nohf).

python report/fill_numbers.py            # write report/numbers.json and fill all documents
python report/fill_numbers.py --check    # fail if a document has a marker whose value differs (or an unknown key)
"""

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TRACK = HERE.parent
REPO = TRACK.parent
DATA = TRACK / "data"
DOCS = [
    TRACK / "technical_report.md",
    TRACK / "docs" / "DATA_CARD.md",
    TRACK / "hf" / "README.template.md",
    TRACK / "data" / "README.md",
    REPO / "README.md",
    REPO / "website" / "index.html",
    REPO / "website" / "pitch" / "index.html",
]
MARK = re.compile(r"<!--n:([A-Za-z0-9_]+)-->(.*?)<!--/n-->", re.S)
PENDING = "[[NIKLAS-PRÜFUNG: {}]]"
# Public pages (website/) never show the raw marker: a neutral text is visible, the marker stays as an HTML comment inside
# the same <!--n:KEY-->…<!--/n--> span, so filling in the real value replaces text and marker together.
PENDING_WEB = "pending (human check in progress – results on 16 October)<!--[[NIKLAS-PRÜFUNG: {}]]-->"
PENDING_WEB_TEXT = {
    "hf_url": "Hugging Face link follows on 16 October<!--[[NIKLAS-PRÜFUNG: {}]]-->"
}
M8, M70 = "apertus-v1.5-8b", "apertus-v1.5-70b"


def load(name, base=DATA):
    p = base / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def pct(x, d=1):
    return f"{100 * x:.{d}f}"


def ci(w):
    return f"{100 * w[0]:.0f}–{100 * w[1]:.0f}"


def judge_label(name):
    return {
        "qwen/qwen3-235b-a22b-2507": "Qwen3-235B-A22B-2507 (Alibaba, open weights)",
        "z-ai/glm-5.3": "GLM-5.3 (Z.ai, open weights)",
        "mistralai/mistral-large-2512": "Mistral Large 3 (Mistral AI, EU, open weights)",
        "deepseek/deepseek-v3.2": "DeepSeek V3.2 (DeepSeek, open weights)",
    }.get(name, name)


def compute():
    n = {}
    fr = load("FREEZE.json")
    st = fr["stats"]
    n.update(
        version=fr["version"],
        cores=st["cores"],
        rows=st["rows"],
        trilingual=st["trilingual_cores"],
        de_only=st["cores"] - st["trilingual_cores"],
        stale_pairs=st["stale_pair_cores"],
        changed_cores=st["temporal_changed_cores"],
        yes_no_share=pct(st["yes_no_share"], 0),
    )
    for k, v in st["by_question_type"].items():
        n[f"qt_{k}"] = v
    for k, v in st["by_generator"].items():
        n[f"gen_{k}"] = v
    for k, v in st["by_bucket"].items():
        n[f"bucket_{k}"] = v
    n["acts"] = len(st["by_act"])
    acts = sorted(st["by_act"].items(), key=lambda kv: -kv[1])
    top, rest = acts[:11], acts[11:]
    if rest:
        top.append((f"{len(rest)} more", sum(v for _, v in rest)))
    mx = max(v for _, v in top)
    n["pitch_act_bars"] = (
        "".join(
            f'\n          <div class="bar">\n            <b>{a}</b><i style="width: {100 * v / mx:.1f}%"></i><span>{v}</span>\n          </div>'
            for a, v in top
        )
        + "\n          "
    )
    bk = st["by_bucket"]
    colors = {
        "stable_pre2024": "navy",
        "changed_2024_2025": "green",
        "changed_2026": "grey-ink",
    }
    n["pitch_bucket_stack"] = (
        "".join(
            f'\n            <div style="width: {100 * bk.get(b, 0) / st["cores"]:.1f}%; background: var(--{c})">{bk.get(b, 0)}</div>'
            for b, c in colors.items()
        )
        + "\n          "
    )
    n["stored_answers"] = (
        f"{sum(len([x for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]) for p in (DATA / 'responses').glob('*.jsonl')):,}"
    )
    ex = load("expected_results.json")
    n["replay_blocks"] = len(ex["results"]) if ex else None
    rows = [
        json.loads(x)
        for x in (DATA / f"merged.v{fr['version']}.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if x.strip()
    ]
    de = [r for r in rows if r["lang"] == "de-CH"]
    for reg in ("lay", "professional"):
        n[f"reg_{reg}"] = sum(r["register"] == reg for r in de)
    n["stale_pairs_nemotron"] = sum(
        1 for r in de if r.get("outdated_answers") and r["generator"] == "nemotron"
    )
    n["closed_drafted"] = sum(
        1 for r in de if r["generator"] in ("claude", "codex", "gemini")
    )
    n["future_change"] = sum(1 for r in de if r.get("future_change"))
    from collections import Counter

    def dist(key, rename=None):
        c = Counter(key(r) for r in de)
        return ", ".join(f"{(rename or {}).get(k, k)} {v}" for k, v in c.most_common())

    n["dist_act"] = dist(
        lambda r: r["source"]["act"], {"BVV2": "BVV 2", "BVV3": "BVV 3"}
    )
    n["articles"] = len({(r["source"]["act"], r["source"]["article_id"]) for r in de})
    n["dist_domain"] = dist(
        lambda r: r["domain"],
        {
            "kvg_insured": "health insurance (insured)",
            "kvg_billing": "health insurance (billing)",
            "ahv": "AHV",
            "iv_el": "IV/EL",
            "uvg_atsg": "accident insurance/ATSG",
            "eo_alv": "EO/ALV",
            "bvg_3a": "occupational pensions & 3a",
            "or_illness": "wage during illness (OR)",
            "famz": "family allowances",
        },
    )
    n["dist_answer_type"] = dist(
        lambda r: r["answer_type"], {"currency_chf": "CHF amount", "yes_no": "yes/no"}
    )
    n["dist_difficulty"] = ", ".join(
        f"{k}: {v}"
        for k, v in sorted(Counter(r["difficulty_prior"] for r in de).items())
    )
    n["dist_stale_gen"] = (
        dist(lambda r: r["generator"].capitalize())
        if False
        else ", ".join(
            f"{k.capitalize()} {v}"
            for k, v in Counter(
                r["generator"] for r in de if r.get("outdated_answers")
            ).most_common()
        )
    )
    n["with_near_miss"] = sum(1 for r in de if r.get("near_miss_answers"))
    n["with_variants"] = sum(1 for r in de if r.get("answer_aliases"))
    n["without_variants"] = len(de) - n["with_variants"]
    n["without_variants_yn"] = sum(
        1 for r in de if not r.get("answer_aliases") and r["answer_type"] == "yes_no"
    )
    sys.path.insert(0, str(TRACK / "src"))
    import coverage

    n["coverage_table"] = "\n\n" + coverage.matrix(DATA) + "\n\n"
    n["status_reviewed"] = fr.get("review_status_cores", {}).get("reviewed", 0)
    n["status_auto"] = fr.get("review_status_cores", {}).get("auto_verified", 0)
    n["frozen_at"] = fr["frozen_at"][:10]
    n["patched_variants_cores"] = len(
        {
            r["core_id"]
            for r in rows
            for m in ((r.get("authoring") or {}).get("manual_correction") or [])
            if isinstance(m, dict) and m.get("review") == "panel-fixes-v1"
        }
    )
    cs = load("contamination.summary.json")
    n.update(
        cont_current=cs["bucket"]["current"],
        cont_outdated=cs["bucket"]["outdated"],
        cont_absent=cs["bucket"]["absent"],
        cont_short=cs["bucket"]["evidence_too_short"],
        cont_temporal_rows=sum(cs["temporal_bucket"].values()),
        cont_temporal_current=cs["temporal_bucket"].get("current", 0),
        cont_temporal_outdated=cs["temporal_bucket"].get("outdated", 0),
        cont_13gram=cs["items_with_question_13gram_hit"],
    )
    vr = (DATA / f"validation_report.v{fr['version']}.md").read_text(encoding="utf-8")
    m = re.search(
        r"(?:Fehler|Errors) \(ERROR\): \*\*(\d+)\*\*.*?(?:Warnungen|warnings) \(WARN\): \*\*(\d+)\*\*",
        vr,
    )
    n.update(validator_errors=int(m.group(1)), validator_warnings=int(m.group(2)))
    warn = {
        c: int(k) for c, k in re.findall(r"^\| WARN ([\w.]+) \| (\d+) \|", vr, re.M)
    }
    n["warn_future"] = warn.get("source.future_change", 0)
    n["warn_threshold"] = warn.get("answer.threshold_word", 0)
    n["warn_discretion"] = warn.get("source.discretion", 0)
    n["warn_other"] = (
        n["validator_warnings"]
        - n["warn_future"]
        - n["warn_threshold"]
        - n["warn_discretion"]
    )
    a = load("analysis.json", HERE)
    for key, m in (("8b", M8), ("70b", M70)):
        x = a["models"][m]
        cd, ob = x["closed_dated"], x["open_book"]
        n[f"correct_{key}"] = pct(cd["all"]["rate"])
        n[f"correct_{key}_ci"] = ci(cd["all"]["wilson95"])
        n[f"stale_rows"] = cd["stale_pair_rows_correct"]["n"]
        n[f"stalepair_correct_{key}"] = pct(cd["stale_pair_rows_correct"]["rate"])
        n[f"stalepair_correct_{key}_ci"] = ci(cd["stale_pair_rows_correct"]["wilson95"])
        n[f"stalepair_stale_{key}"] = pct(cd["stale_pair_rows_stale"]["rate"])
        n[f"stalepair_stale_{key}_ci"] = ci(cd["stale_pair_rows_stale"]["wilson95"])
        n[f"stalepair_na_{key}"] = pct(cd["stale_pair_rows_not_attempted"]["rate"], 0)
        n[f"stalepair_correct_k_{key}"] = cd["stale_pair_rows_correct"]["k"]
        n[f"stalepair_stale_k_{key}"] = cd["stale_pair_rows_stale"]["k"]
        n[f"other_correct_{key}"] = pct(cd["other_rows_correct"]["rate"])
        n[f"other_rows"] = cd["other_rows_correct"]["n"]
        n[f"changed_rows"] = cd["changed_sentence_rows_correct"]["n"]
        n[f"changed_correct_{key}"] = pct(cd["changed_sentence_rows_correct"]["rate"])
        n[f"changed_correct_{key}_ci"] = ci(
            cd["changed_sentence_rows_correct"]["wilson95"]
        ).replace("–", "–")
        n[f"openbook_all_{key}"] = pct(ob["all"]["rate"])
        n[f"openbook_stalepair_{key}"] = pct(ob["stale_pair_rows_correct"]["rate"])
        n[f"openbook_stalepair_{key}_ci"] = ci(
            ob["stale_pair_rows_correct"]["wilson95"]
        )
        n[f"cores_with_stale_answer_{key}"] = x["stale_pair_cores"][
            "with_stale_answer_in_any_language"
        ]
        for b in ("current", "absent", "outdated"):
            e = x["exposure"].get(b)
            if e:
                n[f"exp_{b}_rows"] = e["correct"]["n"]
                n[f"exp_{b}_correct_{key}"] = pct(e["correct"]["rate"])
                n[f"exp_{b}_correct_{key}_r"] = pct(e["correct"]["rate"], 0)
                n[f"exp_{b}_correct_{key}_ci"] = ci(e["correct"]["wilson95"])
                n[f"exp_{b}_stale_{key}"] = pct(e["stale"]["rate"])
                n[f"exp_{b}_stale_{key}_ci"] = ci(e["stale"]["wilson95"])
        sw, pl = (
            x["ablation_de"]["closed_dated_vs_closed_swiss"],
            x["ablation_de"]["closed_dated_vs_closed_plain"],
        )
        n[f"date_effect_{key}"] = (
            f"{100 * (sw['closed_dated_correct'] - sw['closed_swiss_correct']):+.1f}".replace(
                "-", "−"
            )
        )
        n[f"date_p_{key}"] = (
            f"{sw['mcnemar_exact_p']:.2f}".rstrip("0").rstrip(".")
            if sw["mcnemar_exact_p"] < 1
            else "1.0"
        )
        n[f"date_discordant_{key}"] = (
            f"{sw['only_dated_correct']} vs {sw['only_closed_swiss_correct']}"
        )
        n[f"prompt_effect_{key}"] = (
            f"{100 * (pl['closed_dated_correct'] - pl['closed_plain_correct']):+.1f}".replace(
                "-", "−"
            )
        )
        n[f"prompt_p_{key}"] = f"{pl['mcnemar_exact_p']:.2f}"
        for lang in ("de-CH", "fr-CH", "it-CH"):
            n[f"lang_{lang[:2]}_{key}"] = pct(x["by_lang_correct"][lang]["rate"], 0)
        n[f"same_grade_{key}"] = pct(
            x["language_consistency"]["same_grade_all_three"], 0
        )
        n[f"stable_correct_{key}"] = None
    vs = a["70b_vs_8b_closed_dated"]
    n.update(only_70b=vs["only_70b"], only_8b=vs["only_8b"])
    res = load("results.json")
    for key, m in (("8b", M8), ("70b", M70)):
        o = res[f"{m}__closed_dated"]["overall"]
        n[f"incorrect_{key}"] = pct(o["incorrect"])
        n[f"na_{key}"] = pct(o["not_attempted"])
        n[f"f_{key}"] = f"{o['f']:.2f}"
        n[f"stable_correct_{key}"] = pct(
            res[f"{m}__closed_dated"]["by_temporal"]["stable_pre2024"]["correct"]
        )
        n[f"openbook_gain_{key}"] = (
            f"{100 * (res[f'{m}__open_book']['overall']['correct'] - o['correct']):+.0f}"
        )
    qnames = {
        "numeric": "numeric (amount, rate, deadline)",
        "procedural": "procedural (body, step)",
        "yes_no": "yes/no (50 % guessing rate)",
        "temporal": "temporal (rule changed)",
        "calc": "calculation (derived from cited values)",
        "false_premise": "false premise",
        "term": "legal term",
    }
    q8 = res[f"{M8}__closed_dated"]["by_question_type"]
    q70 = res[f"{M70}__closed_dated"]["by_question_type"]
    rows_q = [
        "| Question type | rows | 8B correct | 70B correct | 70B not attempted | 70B stale share of errors |",
        "| --- | --: | --: | --: | --: | --: |",
    ]
    for k in sorted(q70, key=lambda k: -q70[k]["n"]):
        a8, a70 = q8.get(k, {}), q70[k]
        rows_q.append(
            f"| {qnames.get(k, k)} | {a70['n']} | {pct(a8.get('correct', 0))} % | {pct(a70['correct'])} % | "
            f"{pct(a70['not_attempted'])} % | {pct(a70.get('stale_share_of_errors', 0))} % |"
        )
        n[f"qt_{k}_70b"] = pct(a70["correct"], 0)
        n[f"qt_{k}_8b"] = pct(a8.get("correct", 0), 0)
        n[f"qt_{k}_rows"] = a70["n"]
    n["qtype_table"] = "\n\n" + "\n".join(rows_q) + "\n\n"
    n["size_gain_stable"] = (
        f"{float(n['stable_correct_70b']) - float(n['stable_correct_8b']):.0f}"
    )
    n["size_gain_changed"] = (
        f"{float(n['changed_correct_70b']) - float(n['changed_correct_8b']):.0f}"
    )
    p = load("judge_panel.json")
    if p:
        n["panel_judges"] = ", ".join(judge_label(j) for j in p["judges"])
        n["panel_size"] = len(p["judges"])
        n["fleiss_kappa"] = f"{p['fleiss_kappa_3class']:.2f}"
        n["fleiss_kappa_5"] = f"{p['fleiss_kappa_5class']:.2f}"
        n["panel_unanimous"] = pct(p["unanimous_share_3class"], 0)
        n["panel_no_majority"] = p["no_majority_rows"]
        n["panel_rows"] = p["n_rows"]
        n["panel_agreement"] = "; ".join(
            f"{judge_label(j).split(' (')[0]} {pct(v)} %"
            for j, v in p["agreement_with_majority"].items()
        )
        n["panel_cost"] = f"{sum(p['judging_cost_usd'].values()):.2f}"
        cals = []
        for j in p["judges"]:
            c = load(f"judge_calibration__{j.replace('/', '_')}.json") or (
                load("judge_calibration.json")
                if j == "qwen/qwen3-235b-a22b-2507"
                else None
            )
            if c:
                cals.append(
                    f"{judge_label(j).split(' (')[0]} {round(c['grade_accuracy'] * c['n'])}/{c['n']}"
                )
        n["panel_calibration"] = ", ".join(cals)
        n["panel_short"] = " · ".join(
            judge_label(j).split(" (")[0] for j in p["judges"]
        )
    for j, f in (
        ("qwen", "judge_calibration.json"),
        ("glm", "judge_calibration__z-ai_glm-5.3.json"),
        ("mistral", "judge_calibration__mistralai_mistral-large-2512.json"),
    ):
        c = load(f)
        if c:
            n[f"cal_{j}"] = f"{round(c['grade_accuracy'] * c['n'])}/{c['n']}"
    ag = load("judge_agreement_qwen_vs_apertus70b.json")
    if ag:
        b = ag["by_model"]
        n["selfpref_kappa_70b"] = f"{b[M70]['kappa']:.2f}"
        n["selfpref_kappa_8b"] = f"{b[M8]['kappa']:.2f}"
        n["selfpref_extra_70b"] = (
            b[M70]["grades_b"]["CORRECT"] - b[M70]["grades_a"]["CORRECT"]
        )
        n["selfpref_extra_8b"] = (
            b[M8]["grades_b"]["CORRECT"] - b[M8]["grades_a"]["CORRECT"]
        )
    sm = load("human_labels/sample_meta.json")
    n.update(
        sample_cores=sum(sm["dataset_sample"].values()),
        sample_stale=sm["dataset_sample"].get("stale"),
        sample_other=sm["dataset_sample"].get("other"),
        judge_sample=sm["judge_sample"],
        judge_share=pct(sm["judge_sample"] / n["rows"], 0),
    )
    hf = DATA / "hf_url.txt"
    if hf.exists() and hf.read_text(encoding="utf-8").strip():
        n["hf_url"] = hf.read_text(encoding="utf-8").strip()
        n["hf_link"] = f'<a href="{n["hf_url"]}">dataset on Hugging Face</a>'
    hs = load("human_labels/summary.json")
    if hs:
        dc = hs["dataset_check"]
        ja = hs["judge_agreement"]
        n.update(
            human_drops=sum(v["drop"] for v in dc.values()),
            human_checked=sum(v["n"] for v in dc.values()),
            human_unsure=sum(v["unsure"] for v in dc.values()),
            human_err_stale=f"{dc['stale']['drop']} of {dc['stale']['n']}",
            human_err_stale_ci=ci(dc["stale"]["error_rate_wilson95"]),
            human_err_other=f"{dc['other']['drop']} of {dc['other']['n']}",
            human_err_other_ci=ci(dc["other"]["error_rate_wilson95"]),
            kappa_qwen=f"{ja['kappa']:.2f}",
            kappa_qwen_ci=f"{ja['kappa_ci95'][0]:.2f}–{ja['kappa_ci95'][1]:.2f}",
            agree_qwen=pct(ja["raw_agreement"]),
            kappa_qwen_de=f"{ja['by_language_group']['de (original only)']['kappa']:.2f}",
            kappa_qwen_frit=f"{ja['by_language_group']['fr/it (human with machine translation)']['kappa']:.2f}",
            human_labels=ja["n"],
            human_annotator=hs["annotator"],
        )
        if ja.get("vs_panel"):
            vp = ja["vs_panel"]
            n.update(
                kappa_panel=f"{vp['kappa']:.2f}",
                kappa_panel_ci=f"{vp['kappa_ci95'][0]:.2f}–{vp['kappa_ci95'][1]:.2f}",
                agree_panel=pct(vp["raw_agreement"]),
            )
        log = [
            json.loads(x)
            for x in (DATA / "review" / "human_check_log.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if x.strip()
        ]
        n["human_dropped_list"] = (
            "; ".join(
                f"{e['core_id']} ({e['note'] or 'no note'})"
                for e in log
                if e["decision"] == "drop"
            )
            or "none"
        )
    for k, v in list(
        n.items()
    ):  # rounded variants for headline numbers (pitch, form text)
        if isinstance(v, str) and re.fullmatch(r"\d+\.\d", v) and k + "_r" not in n:
            n[k + "_r"] = f"{float(v):.0f}"
    return {k: v for k, v in n.items() if v is not None}


HUMAN_KEYS = {
    "hf_url",
    "hf_link",
    "human_drops",
    "human_checked",
    "human_unsure",
    "human_err_stale",
    "human_err_stale_ci",
    "human_err_other",
    "human_err_other_ci",
    "kappa_qwen",
    "kappa_qwen_ci",
    "agree_qwen",
    "kappa_qwen_de",
    "kappa_qwen_frit",
    "human_labels",
    "human_annotator",
    "kappa_panel",
    "kappa_panel_ci",
    "agree_panel",
    "human_dropped_list",
}


WHEN = re.compile(
    r"<!--when:(\w+)-->(.*?)<!--/when:\1-->|<!--when:(\w+):off(.*?)/when:\3:off-->",
    re.S,
)


def _esc(s):
    return s.replace("<!--", "<!~~").replace("-->", "~~>")


def _unesc(s):
    return s.replace("<!~~", "<!--").replace("~~>", "-->")


def conditions(n):
    human = "kappa_qwen" in n
    hf = "hf_url" in n
    return {"human": human, "pending": not human, "hf": hf, "nohf": not hf}


def fill(text, n, missing, web=True):
    """Fill <!--n:KEY-->…<!--/n--> markers and switch <!--when:COND-->…<!--/when:COND--> blocks.

    An inactive block is kept as one HTML comment (inner comments escaped), so Markdown, Pandoc and browsers hide it
    and the next run can switch it on again. Conditions: human / pending (human check imported or not), hf / nohf.
    """

    def rep(m):
        k = m.group(1)
        if k in n:
            return f"<!--n:{k}-->{n[k]}<!--/n-->"
        if k in HUMAN_KEYS:
            pending = PENDING_WEB_TEXT.get(k, PENDING_WEB) if web else PENDING
            return f"<!--n:{k}-->{pending.format(k)}<!--/n-->"
        missing.add(k)
        return m.group(0)

    cond = conditions(n)

    def block(m):
        name, body = (
            (m.group(1), m.group(2)) if m.group(1) else (m.group(3), _unesc(m.group(4)))
        )
        if name not in cond:
            missing.add(f"when:{name}")
            return m.group(0)
        body = MARK.sub(rep, body)
        if cond[name]:
            return f"<!--when:{name}-->{body}<!--/when:{name}-->"
        return f"<!--when:{name}:off{_esc(body)}/when:{name}:off-->"

    out, pos = [], 0
    for m in WHEN.finditer(text):
        out.append(MARK.sub(rep, text[pos : m.start()]))
        out.append(block(m))
        pos = m.end()
    out.append(MARK.sub(rep, text[pos:]))
    return "".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    n = compute()
    (HERE / "numbers.json").write_text(
        json.dumps(n, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    missing, changed = set(), []
    for doc in DOCS:
        if not doc.exists():
            continue
        t = doc.read_text(encoding="utf-8")
        new = fill(t, n, missing)
        if new != t:
            changed.append(doc.name)
            if not args.check:
                doc.write_bytes(new.encode("utf-8"))
    pending = sorted(k for k in HUMAN_KEYS if k not in n)
    print(
        f"{len(n)} numbers; documents {'to change' if args.check else 'changed'}: {changed or 'none'}; "
        f"pending human keys: {len(pending)}; unknown keys: {sorted(missing) or 'none'}"
    )
    if missing or (args.check and changed):
        sys.exit(1)


if __name__ == "__main__":
    main()
