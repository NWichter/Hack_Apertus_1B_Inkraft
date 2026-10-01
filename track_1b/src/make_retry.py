"""Build a retry prompt for one batch: same template and article context, extended parameter block."""
import json
import sys
from pathlib import Path
import make_batches as mb

batch_id, rejected_ids, out_dir = sys.argv[1], sys.argv[2].split(","), Path(sys.argv[3])
b = next(x for x in mb.BATCHES if x["id"] == batch_id)
lines = [json.loads(l) for l in (out_dir / f"{batch_id}.out.jsonl").read_text(encoding="utf-8").splitlines() if l.strip().startswith("{")]
first = int(sys.argv[4])
rejected = [lines[int(i) - first] for i in rejected_ids]
kept = [l for k, l in enumerate(lines) if str(k + first) not in rejected_ids]
reasons = json.loads(sys.argv[5])
art_ids = [a for ids in b["domains"].values() for a in ids]
params = "\n".join([
    f"ACT: {b['act']}",
    f"N_ITEMS: {len(rejected)}",
    "QUOTA: numeric=2, procedural=2, yes_no=2, temporal=0",
    "ARTICLES AND DOMAIN:",
    *[f"  {d}: {', '.join(ids)}" for d, ids in b["domains"].items()],
    "CHANGED ARTICLES (temporal allowed): none",
    "PARALLEL: yes",
    "RETRY: these items replace rejected drafts. Rejected drafts (do not repeat them):",
    *[f"  - {r['de']['question']} -> rejected because: {reasons[str(rid)]}" for rid, r in zip(rejected_ids, rejected)],
    "EXISTING ITEMS (do not repeat these facts):",
    *[f"  - {k['de']['question']}" for k in kept],
])
articles = "\n\n".join(mb.render_article(b["act"], a, a in b["changed"]) for a in art_ids)
prompt = (mb.TEMPLATE.replace("{N_ITEMS}", str(len(rejected))).replace("{MAX_PER_ARTICLE}", "3")
          .replace("{BATCH_PARAMETERS}", params).replace("{ARTICLES}", articles))
(out_dir / f"{batch_id}_r1.prompt.txt").write_text(prompt, encoding="utf-8")
print(len(prompt))
