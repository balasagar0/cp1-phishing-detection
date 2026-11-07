# Privacy and ethics (R3-16)

What this code stores, hashes, logs and deletes, and for how long. Every statement points to the code that makes it true and the test that checks it.

## What each part keeps

| Part | Keeps | Does not keep |
|---|---|---|
| `POST /score`, `/score/batch`, `/correlate` | nothing: the message is scored in memory and the answer returned | the message, the sender, the result |
| `POST /events` (event store, `src/event_store.py`) | per event: channel, time, score, label, model version, the identity tokens **as HMAC-SHA256**, the recipient **as HMAC-SHA256**, the time it was stored | the message text and subject, unless `CP1_STORE_CONTENT=1` is set before the API starts |
| Campaigns and alerts (same database) | which stored events form a campaign, its risk, the hashed shared tokens, the alert's reason (event numbers, channels, scores, token kind and the first 8 hex digits of its hash) | any plain identity token or text |
| Logs | none from the application. Start uvicorn with `--no-access-log` (as `start_demo.bat`, `RUN_DEMO.bat`, `scripts/preflight.py` and the benchmark do): uvicorn's access log would print request paths, and `GET /campaigns?recipient=` would put a recipient in clear in that log | message text, recipients, tokens |
| Console (browser) | nothing beyond the page's own memory; no cookies, no local storage, no outside requests | – |

Checks: `tests/test_event_store.py::test_recipient_tokens_and_text_are_not_stored_in_clear` reads the raw database file and finds no recipient, domain, phone number or message text. NFR-06 in `tests/test_final_cases.py` sends a marker message through `/score`, `/correlate` and `/events` and finds it in no output, no log, no changed file and not in the database.

## Hashing

- Algorithm: HMAC-SHA256 (`EventStore.h`, `EventStore.htok` in `src/event_store.py`). A token keeps its kind (`dom:`, `tel:`, `id:`) so that two events can still be matched; the value itself is hashed.
- Key: the environment variable `CP1_HMAC_KEY`, or else a random 256-bit key generated once into `.cp1_hmac_key` in the project folder (`load_key`). That file is in `.gitignore` and must never be shared: anyone with the key and a guess (a phone number, say) could confirm the guess.
- The same key must be kept for the life of the database; a new key makes old hashes unmatchable (old events stop linking to new ones).

## Deletion and retention

- `POST /purge {"older_than_days": N}` deletes events stored more than N days ago, alerts raised before then, and the campaigns left empty (`EventStore.purge`). With no body it uses `CP1_RETENTION_DAYS`, default 30. Tested by `test_purge_deletes_old_events_and_their_campaigns`.
- The purge is not run automatically. Whoever runs a deployment must schedule it. Deleting `data/events.db` removes everything at once.
- `POST /alerts/{id}/ack` marks an alert as seen; it does not delete it.

## Data used to build the models

See `DATA_SOURCES.md`: every public dataset, its source, its licence or terms as checked, and its SHA-256. No dataset is committed to git. Some sources have no stated licence; they must be checked before the models or data are published.

## The team's own emails (email model v3)

The full account of this pipeline, with each claim's test and status, is `PRIVACY_AND_ETHICS.md` at the project root. In short:

- The v3 email attempt can train on the account owner's own legitimate emails (receipts, bank, order, shipping, OTP and account notices), exported by them as .mbox into `data/raw/email_own/`. This is used only with the owner's consent, which was given on 7 Nov 2026.
- The export stays on this laptop: `data/` is gitignored, and nothing from it is committed, uploaded or used as a test case. Delete the folder to withdraw it; retrain afterwards.
- The model keeps only words that appear in at least five emails of at least two different sources, and numbers are masked, so names, order numbers and amounts from one inbox do not enter the model. The trained model file still derives from the mail: do not publish it while the export is in its training data.
- Only mail the owner has checked is legitimate goes in. Messages Gmail filed as Spam or Trash are skipped.
- **Outcome:** v3 was not adopted. It failed the adoption rule and its privacy audit (`reports/privacy/email_v3_privacy_audit.md`). The live
  email model is v2's, which never saw this mail. The v3 model file and the export stay on this laptop only, outside git; deleting them is the
  owner's choice.

## Ethics notes

- **Consent for real bundles (R2-10).** Messages collected for the real-bundle evaluation must come from the team's own accounts or from people who agreed in writing. `TESTCASE_FORMAT.md` requires a `basis` for every `collected_real` row. Never create or fake bundles.
- **Voice and video are not built.** Calls and video are shown as "not assessed", never as safe.
- **Simulated results are labelled simulated.** The correlation model was trained on simulated bundles; its risk is not a calibrated probability.
- **Hand-written samples are not a test set.** No rate is computed from them in any document.
- **Mistakes cost people.** A false alarm on a real bank alert (D-16) or a missed phishing email (D-17) both happen with this build; the console and reports say so.
- **Patent privacy.** No git remote, no upload of code, data, models or reports until the patent is filed (rule 8, PT-10).
