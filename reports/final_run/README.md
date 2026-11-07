# Final run record (Phase 4.1)

Written by `scripts/final_run_record.py` on 2026-11-07T16:26:12+05:30. Every number below is computed by that script.

`download_data.sh` and `run_all.sh` ran on `cp1-rc1` (commit `7761903`). This folder holds the reports that run wrote (`*.json`, `results.md`, `log_*.txt`, `run_all_log.txt`). The models it trained are kept on the build laptop in `models/candidates/final_run/` and are not committed; `model_manifest.json` here lists their hashes.

## Decision

**Not adopted.** not adopted: the account owner chose on 7 Nov 2026 to keep v2's models live, applying the same adoption rule as Phase 3. Rule (c) says the demo cases' alert outcomes are kept; it fails on TC-06. The shipped models are v2's, and `reports/` describes them.

## What changed and why

The only training change since v2 is the email text cleaner fix (D-11, D-15: drop scripts and styles, keep link targets). The simulation pools for SMS and URL are identical; the email pool differs. Email honest F1 (mean of three leave-one-corpus-out runs): live 82.2%, retrained 82.1%. Simulated 60-minute engine F1: live 92.0%, retrained 92.1%. Every figure is compared value by value in `reports/final_run_check.md`.

## Demo cases (hand-written, not a test set)

| Case | Live models: events, bundle, alert | Retrained models: events, bundle, alert | Alert outcome kept |
|---|---|---|---|
| TC-01 | [0.998], 0.998, alert | [0.998], 0.998, alert | yes |
| TC-02 | [1.0], 1.0, alert | [1.0], 1.0, alert | yes |
| TC-03 | CANNOT_ASSESS (calls are not assessed) | CANNOT_ASSESS (calls are not assessed) | yes |
| TC-04 | [1.0, 0.995, 0.998], 1.0, alert | [1.0, 0.995, 0.998], 1.0, alert | yes |
| TC-05 | [0.002, 0.0, 0.0], 0.0, no alert | [0.002, 0.0, 0.0], 0.0, no alert | yes |
| TC-06 | [0.421, 0.451, 0.204], 0.595, alert | [0.421, 0.452, 0.208], 0.456, no alert | **no** |
| TC-07 | [0.421, 0.451, 0.204], 0.451, no alert | [0.421, 0.452, 0.208], 0.452, no alert | yes |
| TC-08 | [0.97, 0.031], 1.0, alert | [0.97, 0.031], 1.0, alert | yes |

## Which model moves TC-06

| Detectors | Correlation model | TC-06 bundle risk | TC-07 bundle risk |
|---|---|---|---|
| live | live | 0.595 | 0.451 |
| live | retrained | 0.456 | 0.451 |
| retrained | live | 0.595 | 0.452 |
| retrained | retrained | 0.456 | 0.452 |

The drop comes from the retrained correlation model; the detectors barely move. The simulated metrics hardly change, so the correlation model's verdict on a weak, borderline bundle is not stable under a retrain on almost the same simulated data. Real bundles (R2-10) are needed to settle it.
