"""Phase 3.3 (R2-02, D-09, D-16): the live SMS model on the workbook SMS, by lure type.  python scripts/sms_lure_report.py
HAND-WRITTEN, NOT A TEST SET: 32 messages, one or two per lure type, so these are per-message results, not rates to quote.
The alert score is the one the API uses for SMS: 1 - P(ham) (spam or smishing). Writes reports/candidates/sms_d09.md and .json."""
import json, sys, datetime
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
from predict import Detectors

SEARCH = ("No SMS retrain. The brief allows one only with real smishing data whose source and licence can be checked. "
          "The SMS data v2 already uses (LSDST, 5,971 raw messages) is the Mishra and Soni 'SMS Phishing Dataset for Machine Learning and Pattern Recognition' "
          "(Mendeley Data, DOI 10.17632/f45bkkt8pr.1, CC BY 4.0): same row and class counts. A search for a public set of legitimate transactional SMS "
          "(bank alerts, bills), which is what D-16 needs, found none with a stated licence. So D-09 and D-16 stay open.")


def main():
    D = Detectors(); wb = json.loads((ROOT / "tests" / "data" / "workbook_cases.json").read_text(encoding="utf-8"))["sms"]
    rows = []
    for r in wb:
        j = D.score_sms(r["Message"]); pred = "Phishing" if j["score"] >= .5 else "Legitimate"
        rows.append({"id": r["ID"], "group": r["Group"], "lure": r["Category"], "expected": r["Expected label"], "score": j["score"], "smishing_probability": j["smishing_probability"],
                     "predicted": pred, "right": pred == r["Expected label"]})
    miss = [x for x in rows if x["expected"] == "Phishing" and not x["right"]]; fa = [x for x in rows if x["expected"] == "Legitimate" and not x["right"]]
    nP, nL = sum(x["expected"] == "Phishing" for x in rows), sum(x["expected"] == "Legitimate" for x in rows)
    res = {"date": datetime.datetime.now().astimezone().isoformat(timespec="seconds"), "rows": rows, "missed_phishing": [x["id"] for x in miss], "flagged_legitimate": [x["id"] for x in fa],
           "n_phishing": nP, "n_legitimate": nL, "data_search": SEARCH}
    (ROOT / "reports" / "candidates").mkdir(parents=True, exist_ok=True)
    (ROOT / "reports" / "candidates" / "sms_d09.json").write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    pct = lambda x: f"{100 * x:.1f}%"
    L = ["# SMS by lure type (Phase 3.3, D-09 and D-16)\n", f"Written by `scripts/sms_lure_report.py` on {res['date']}. **Hand-written, not a test set**: one or two messages per lure type, "
         "so each row is one message's result, not a rate. Alert score = 1 - P(ham), the score the API uses for SMS.\n",
         f"Phishing messages missed: {len(miss)} of {nP} ({', '.join(x['id'] for x in miss) or 'none'}). Legitimate messages flagged: {len(fa)} of {nL} ({', '.join(x['id'] for x in fa) or 'none'}).\n",
         "| ID | Group | Lure or message type | Expected | Alert score | P(smishing) | Result |", "|---|---|---|---|---|---|---|"]
    L += [f"| {x['id']} | {x['group']} | {x['lure']} | {x['expected']} | {pct(x['score'])} | {pct(x['smishing_probability'])} | {'right' if x['right'] else '**wrong**'} |" for x in rows]
    L += ["", "## Data and decision\n", SEARCH, "",
          "**Proposed: accept D-09 because** the fault it describes (phishing-style SMS missed: 1 of 12 caught on the old build) no longer shows on v2: the misses above are the only ones, "
          "and the honest held-out measure is smishing-vs-rest F1 in reports/sms_metrics.json. SMS-03 still fails on its legitimate half, which is D-16. The team decides.",
          "", "**D-16 stays open.** Legitimate transactional SMS (bank alerts, bill reminders) are flagged because the training set has few of them. Fixing it needs real legitimate transactional SMS "
          "with a clear licence, or the team's own messages collected with consent (as for R2-10)."]
    (ROOT / "reports" / "candidates" / "sms_d09.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L[2:3]))


if __name__ == "__main__":
    main()
