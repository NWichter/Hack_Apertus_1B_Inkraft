"""Fetch Swiss federal acts from fedlex (DE/FR/IT) and split them into articles.

Selects, per act, the consolidation applicable on AS_OF, the one applicable on
PREVIOUS_CUTOFF (for "changed since 2024" items) and every already published
future consolidation (to flag articles that will change after AS_OF).
"""

import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

from bs4 import BeautifulSoup

SPARQL = "https://fedlex.data.admin.ch/sparqlendpoint"
AS_OF = "2026-10-01"
PREVIOUS_CUTOFF = "2023-12-31"
LANGS = {"DEU": "de", "FRA": "fr", "ITA": "it"}

ACTS = {
    "830.1": "ATSG",
    "831.10": "AHVG",
    "831.20": "IVG",
    "831.30": "ELG",
    "832.10": "KVG",
    "832.102": "KVV",
    "832.20": "UVG",
    "220": "OR",
    "834.1": "EOG",
    "837.0": "AVIG",
    "831.40": "BVG",
    "831.441.1": "BVV2",
    "831.461.3": "BVV3",
}

QUERY = """
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
SELECT DISTINCT ?sr ?act ?date ?lang ?file WHERE {
  ?act a jolux:ConsolidationAbstract ; jolux:classifiedByTaxonomyEntry/skos:notation ?sr .
  FILTER(STR(?sr) IN (%s))
  ?cons jolux:isMemberOf ?act ; jolux:dateApplicability ?date ; jolux:isRealizedBy ?expr .
  ?expr jolux:language ?lang ; jolux:isEmbodiedBy ?m .
  ?m jolux:userFormat <https://fedlex.data.admin.ch/vocabulary/user-format/html> ; jolux:isExemplifiedBy ?file .
  FILTER(?lang IN (<http://publications.europa.eu/resource/authority/language/DEU>,
                   <http://publications.europa.eu/resource/authority/language/FRA>,
                   <http://publications.europa.eu/resource/authority/language/ITA>))
}
"""

TITLE_QUERY = """
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
SELECT ?act ?lang ?title WHERE {
  VALUES ?act { %s }
  ?act jolux:isRealizedBy ?e . ?e jolux:language ?lang ; jolux:title ?title .
  FILTER(?lang IN (<http://publications.europa.eu/resource/authority/language/DEU>,
                   <http://publications.europa.eu/resource/authority/language/FRA>,
                   <http://publications.europa.eu/resource/authority/language/ITA>))
}
"""

UA = {
    "User-Agent": "stichtag-dataset-builder/0.1 (research; public-domain legal texts)"
}


def sparql_csv(query):
    data = urllib.parse.urlencode({"query": query}).encode()
    req = urllib.request.Request(
        SPARQL, data=data, headers={**UA, "Accept": "text/csv"}
    )
    with urllib.request.urlopen(req, timeout=180) as r:
        return list(csv.DictReader(io.StringIO(r.read().decode("utf-8"))))


def download(url, cache_dir):
    target = cache_dir / hashlib.sha1(url.encode()).hexdigest()
    if target.exists():
        return target.read_bytes()
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=120) as r:
                body = r.read()
            target.write_bytes(body)
            time.sleep(0.5)
            return body
        except Exception:
            if attempt == 3:
                raise
            time.sleep(3 * (attempt + 1))


def clean(text):
    text = text.replace("\xa0", " ").replace(" ", " ").replace(" ", " ")
    return re.sub(r"\s+", " ", text).strip()


def parse_articles(html):
    soup = BeautifulSoup(html, "lxml")
    for br in soup.find_all("br"):
        br.replace_with(" ")
    for sup in soup.select("sup"):
        if sup.find("a", href=re.compile(r"^#fn-")):
            sup.decompose()
    for fn in soup.select("div.footnotes"):
        fn.decompose()
    articles = {}
    for art in soup.find_all("article"):
        art_id = art.get("id", "")
        if not art_id.startswith("art_") and "/art_" not in art_id:
            continue
        head = art.find(["h6", "h5"], class_="heading")
        heading = clean(head.get_text(" ")) if head else ""
        m = re.match(
            r"(Art\.?|Article|Articolo)\s*([0-9]+[a-z]*(?:\s*(?:bis|ter|quater|quinquies|sexies|septies|octies|novies|decies))?)",
            heading,
        )
        number = art_id.split("art_")[-1].replace("_", "")
        body = art.find("div", class_="collapseable") or art
        paragraphs = []
        current = None
        for el in body.find_all(["p", "dl"], recursive=True):
            if el.find_parent("dl") is not None and el.name == "p":
                continue
            if el.name == "p":
                sup = el.find("sup")
                num = (
                    clean(sup.get_text())
                    if sup and el.contents and el.contents[0] is sup
                    else ""
                )
                if sup and num:
                    sup.extract()
                text = clean(el.get_text(""))
                if not text:
                    continue
                current = {"paragraph": num, "text": text}
                paragraphs.append(current)
            elif el.name == "dl":
                if el.find_parent("dl") is not None:
                    continue
                items = []
                for dt_el in el.find_all("dt", recursive=False):
                    dd = dt_el.find_next_sibling("dd")
                    items.append(
                        clean(dt_el.get_text(""))
                        + " "
                        + (clean(dd.get_text("")) if dd else "")
                    )
                block = " ".join(items)
                if current is None:
                    current = {"paragraph": "", "text": ""}
                    paragraphs.append(current)
                current["text"] = (current["text"] + " " + block).strip()
        text = "\n".join(
            ((p["paragraph"] + " ") if p["paragraph"] else "") + p["text"]
            for p in paragraphs
        )
        key = art_id
        articles[key] = {
            "article_id": art_id,
            "number": number,
            "heading": heading,
            "paragraphs": paragraphs,
            "text": text,
        }
    return articles


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--cache", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    cache = Path(args.cache)
    out.mkdir(parents=True, exist_ok=True)
    cache.mkdir(parents=True, exist_ok=True)

    rows = sparql_csv(QUERY % ",".join(f'"{sr}"' for sr in ACTS))
    by_act = {}
    for r in rows:
        lang = LANGS[r["lang"].rsplit("/", 1)[-1]]
        a = by_act.setdefault(r["sr"], {"eli": r["act"], "versions": {}})
        a["versions"].setdefault(r["date"], {})[lang] = r["file"]

    acts_values = " ".join(f"<{a['eli']}>" for a in by_act.values())
    titles = {}
    for r in sparql_csv(TITLE_QUERY % acts_values):
        titles.setdefault(r["act"], {})[LANGS[r["lang"].rsplit("/", 1)[-1]]] = r[
            "title"
        ]

    manifest = {
        "as_of": AS_OF,
        "previous_cutoff": PREVIOUS_CUTOFF,
        "retrieved_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "source": "https://fedlex.data.admin.ch (SPARQL endpoint + filestore HTML manifestations)",
        "license": "public-domain-ch-urg-art5",
        "license_note": "Federal acts are not protected by copyright (Art. 5 para. 1 lit. a URG, SR 231.1).",
        "acts": [],
    }

    for sr, abbr in ACTS.items():
        info = by_act[sr]
        dates = sorted(info["versions"])
        current = max(d for d in dates if d <= AS_OF)
        prev_candidates = [d for d in dates if d <= PREVIOUS_CUTOFF]
        previous = max(prev_candidates) if prev_candidates else None
        future = [d for d in dates if d > AS_OF]
        selected = [("current", current)]
        if previous and previous != current:
            selected.append(("previous", previous))
        intermediate = [d for d in dates if previous and previous < d < current]
        selected += [("intermediate", d) for d in intermediate]
        selected += [("future", d) for d in future]

        act_entry = {
            "abbr": abbr,
            "sr": sr,
            "eli": info["eli"],
            "title": titles.get(info["eli"], {}),
            "all_consolidation_dates": dates,
            "versions": [],
        }
        parsed = {}
        for role, date in selected:
            langs = ["de", "fr", "it"] if role != "future" else ["de"]
            if role == "previous":
                langs = ["de", "fr", "it"]
            vdir = out / f"{abbr}_SR-{sr}" / date.replace("-", "")
            vdir.mkdir(parents=True, exist_ok=True)
            ventry = {"role": role, "version_date": date, "files": {}}
            for lang in langs:
                file_url = info["versions"][date].get(lang)
                if not file_url:
                    continue
                html = download(file_url, cache)
                arts = parse_articles(html)
                parsed[(date, lang)] = arts
                eli_url = f"{info['eli']}/{date.replace('-', '')}/{lang}"
                payload = {
                    "act": abbr,
                    "sr": sr,
                    "lang": lang,
                    "title": titles.get(info["eli"], {}).get(lang),
                    "version_date": date,
                    "role": role,
                    "eli_url": eli_url,
                    "html_url": file_url,
                    "html_sha256": hashlib.sha256(html).hexdigest(),
                    "license": "public-domain-ch-urg-art5",
                    "articles": [
                        {**a, "url": f"{eli_url}#{a['article_id']}"}
                        for a in arts.values()
                    ],
                }
                fpath = vdir / f"{lang}.json"
                fpath.write_text(
                    json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8"
                )
                ventry["files"][lang] = {
                    "path": str(fpath.relative_to(out)).replace("\\", "/"),
                    "eli_url": eli_url,
                    "html_url": file_url,
                    "html_sha256": payload["html_sha256"],
                    "n_articles": len(arts),
                }
                print(abbr, role, date, lang, len(arts))
            act_entry["versions"].append(ventry)

        cur_de = parsed[(current, "de")]
        if previous and previous != current:
            prev_de = parsed[(previous, "de")]
            act_entry["changed_since_previous"] = sorted(
                k
                for k in cur_de
                if k not in prev_de or prev_de[k]["text"] != cur_de[k]["text"]
            )
        if previous and previous != current:
            chain = [previous] + intermediate + [current]
            change_dates = {}
            for k in act_entry["changed_since_previous"]:
                seen = [d for d in chain if (d, "de") in parsed]
                for i in range(len(seen) - 1, 0, -1):
                    a_new = parsed[(seen[i], "de")].get(k)
                    a_old = parsed[(seen[i - 1], "de")].get(k)
                    if (a_old or {}).get("text") != (a_new or {}).get("text"):
                        change_dates[k] = seen[i]
                        break
            act_entry["last_change_date"] = change_dates
        act_entry["changes_after_as_of"] = {}
        for d in future:
            fut = parsed.get((d, "de"), {})
            act_entry["changes_after_as_of"][d] = sorted(
                k
                for k in set(cur_de) | set(fut)
                if k not in fut
                or k not in cur_de
                or fut[k]["text"] != cur_de[k]["text"]
            )
        manifest["acts"].append(act_entry)

    (out / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
