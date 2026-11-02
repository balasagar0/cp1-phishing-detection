# URL: the scheme and trailing-slash check (Phase 3.2, D-01)

Written by `scripts/check_url_d01.py` on 2026-11-02T12:24:26+05:30.

- URLs checked: 43 (36 workbook URLs, hand-written, plus the demo-case and story URLs). Variants scored: 444 (with and without `http://` or `https://`, `www.` and a trailing slash).
- URLs whose label changes between variants: **0** .
- Every variant of a URL gets the identical score: True (canonicalisation strips all three before scoring).
- Training and serving canonicalise the same way (`canon()` in `src/url_features.py` used by `src/train_url.py` and `src/predict.py`): True.

**Decision: no retrain: no variant changes a label.** The D-01 fault (the old 30-feature model counting the scheme's characters) does not exist in v2's string model.

## The login-page trade-off, both halves (host-grouped test, reports/url_metrics.json)

| Variant | False alarms on login URLs of 1,000 held-out popular domains | Recall on bad URLs hosted on top-10k domains |
|---|---|---|
| first version (n-grams only) | 92.2% | 49.9% (n=381) |
| deployed (popularity flags + login training URLs) | 0.0% | 30.7% (n=381) |

Host-grouped F1 of the deployed model: 90.4%. The login URLs are constructed, not real traffic.

What still fails in D-01's cases: URL-07, where U-H06 (a real Google sign-in URL with a long `continue=` query) is flagged. That is a login-page false alarm on a URL shape the constructed login set does not cover, not the scheme fault.
