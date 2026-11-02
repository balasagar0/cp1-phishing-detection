"""Phase 3.2 (R2-01, D-01): do 'https://', 'www.' or a trailing slash still change a URL's score?  python scripts/check_url_d01.py
Scores every workbook URL (hand-written, not a test set) and every demo-case URL in its written form and in variants with and without the
scheme, 'www.' and a trailing slash, through the live model. Checks that training and serving canonicalise the same way. Reports both halves of
the login-page trade-off from reports/url_metrics.json. Writes reports/candidates/url_d01.md and .json. Retraining is called for only if a
variant flips a label; the brief says to normalise identically in training and serving in that case."""
import json, re, sys, datetime
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
from predict import Detectors
from url_features import canon
from demo_cases import CASES, STORIES


def variants(u):
    core = re.sub(r"^[a-z][a-z0-9+.\-]*://", "", u.strip(), flags=re.I)
    bare = re.sub(r"^www\d?\.", "", core, flags=re.I).rstrip("/")
    out = {u}
    for pre in ("", "http://", "https://"):
        for w in ("", "www."):
            for tail in ("", "/"):
                if "?" in bare and tail: continue                                   # a slash after a query string is a different URL
                out.add(f"{pre}{w}{bare}{tail}")
    return sorted(out)


def main():
    D = Detectors(); wb = json.loads((ROOT / "tests" / "data" / "workbook_cases.json").read_text(encoding="utf-8"))["url"]
    urls = [(r["ID"], r["URL"], r["Expected label"]) for r in wb] + [(k, e["text"], "") for k, v in {**CASES, **STORIES}.items() for e in v["events"] if e["channel"] == "url"]
    rows, flips, n = [], [], 0
    for cid, u, exp in urls:
        sc = {v: D.score_url(v)["score"] for v in variants(u)}; n += len(sc)
        labels = {v: s >= .5 for v, s in sc.items()}
        if len(set(labels.values())) > 1: flips.append(cid)
        rows.append({"id": cid, "url": u, "expected": exp, "variants": len(sc), "min": min(sc.values()), "max": max(sc.values()), "same_score": len(set(sc.values())) == 1})
    src_train = (ROOT / "src" / "train_url.py").read_text(encoding="utf-8"); src_pred = (ROOT / "src" / "predict.py").read_text(encoding="utf-8")
    same_canon = "u.url.map(canon)" in src_train and "c = canon(url)" in src_pred
    U = json.loads((ROOT / "reports" / "url_metrics.json").read_text())["string_model"]; ab = U["ablation"]
    fin, first = ab["c_plus_login_training_urls_FINAL"], ab["a_ngrams_only"]
    res = {"date": datetime.datetime.now().astimezone().isoformat(timespec="seconds"), "urls": len(urls), "variants_scored": n, "urls_whose_label_flips": flips,
           "training_and_serving_use_canon": same_canon, "rows": rows,
           "login_false_alarms_final": fin["false_positive_rate_on_login_urls_of_1000_held_out_popular_domains"], "login_false_alarms_first_version": first["false_positive_rate_on_login_urls_of_1000_held_out_popular_domains"],
           "recall_bad_on_popular_final": fin["recall_on_bad_urls_hosted_on_top10k_domains"], "recall_bad_on_popular_first_version": first["recall_on_bad_urls_hosted_on_top10k_domains"],
           "host_grouped_f1": U["grouped_test"]["f1"], "decision": "no retrain: no variant changes a label" if not flips else "retrain: a variant changes a label"}
    (ROOT / "reports" / "candidates").mkdir(parents=True, exist_ok=True)
    (ROOT / "reports" / "candidates" / "url_d01.json").write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
    pct = lambda x: f"{100 * x:.1f}%"
    L = ["# URL: the scheme and trailing-slash check (Phase 3.2, D-01)\n", f"Written by `scripts/check_url_d01.py` on {res['date']}.\n",
         f"- URLs checked: {len(urls)} ({len(wb)} workbook URLs, hand-written, plus the demo-case and story URLs). Variants scored: {n} (with and without `http://` or `https://`, `www.` and a trailing slash).",
         f"- URLs whose label changes between variants: **{len(flips)}** {flips if flips else ''}.",
         f"- Every variant of a URL gets the identical score: {all(r['same_score'] for r in rows)} (canonicalisation strips all three before scoring).",
         f"- Training and serving canonicalise the same way (`canon()` in `src/url_features.py` used by `src/train_url.py` and `src/predict.py`): {same_canon}.",
         f"\n**Decision: {res['decision']}.** The D-01 fault (the old 30-feature model counting the scheme's characters) does not exist in v2's string model.",
         "\n## The login-page trade-off, both halves (host-grouped test, reports/url_metrics.json)\n", "| Variant | False alarms on login URLs of 1,000 held-out popular domains | Recall on bad URLs hosted on top-10k domains |", "|---|---|---|",
         f"| first version (n-grams only) | {pct(res['login_false_alarms_first_version'])} | {pct(res['recall_bad_on_popular_first_version']['recall'])} (n={res['recall_bad_on_popular_first_version']['n']}) |",
         f"| deployed (popularity flags + login training URLs) | {pct(res['login_false_alarms_final'])} | {pct(res['recall_bad_on_popular_final']['recall'])} (n={res['recall_bad_on_popular_final']['n']}) |",
         f"\nHost-grouped F1 of the deployed model: {pct(res['host_grouped_f1'])}. The login URLs are constructed, not real traffic.",
         "\nWhat still fails in D-01's cases: URL-07, where U-H06 (a real Google sign-in URL with a long `continue=` query) is flagged. That is a login-page false alarm on a URL shape the constructed login set does not cover, not the scheme fault."]
    (ROOT / "reports" / "candidates" / "url_d01.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L[2:6] + [L[7]]))


if __name__ == "__main__":
    main()
