# Privacy and ethics: training on the owner's Gmail export

This file follows the owner's privacy spec of 7 Nov 2026 for training the email model on their own Gmail Takeout export. It covers only that
pipeline. The rest of the system (event store, API, logs) is covered in `docs/PRIVACY.md`.

Status words, as the spec asks:
- **VERIFIED**: proven by implementation and tests.
- **PARTIAL**: protection exists but is incomplete.
- **FAILED**: the requirement is violated.
- **UNVERIFIED**: not enough evidence.

Privacy comes before model performance. No control here was weakened to make training work.

## What is used, and why

The owner exported known-legitimate mail (receipts, bank, order, shipping, OTP and account notices) as one `.mbox` file into
`data/raw/email_own/`, with consent. It gives the email model real modern legitimate mail. Without it, the model learnt that transactional
wording means phishing (`reports/candidates/email_candidates.md`).

No anonymisation, redaction or Presidio-style rewriting is applied: the model learns from the original text, as the spec asks.

## Where email data is processed

| Step | Code | In memory or on disk | How long | Leaves the machine? |
|---|---|---|---|---|
| Original archive | `data/raw/email_own/*.mbox` | on disk, written by the owner | until the owner deletes it | no. `data/` is gitignored; nothing uploads it |
| Reading | `email_stream._raw_messages` opens the file read-only (`rb`) and reads it line by line | memory: the lines of **one** message | until the next message starts | no |
| Parsing | `email_stream.iter_texts` parses one message, skips Spam and Trash, takes the subject and the plain or HTML body. Attachments are never decoded | memory: one message object and its text | until the caller has counted it | no |
| Counting | `private_email_training.stream_private` cleans the text (numbers masked), splits it into word n-grams, and counts **only** n-grams already in the public candidate vocabulary; then drops the text | memory: one row of integer counts per email, plus a hash of each normalised text to drop duplicates | for the training run (minutes) | no |
| Training | `MatrixFeat`, `fit_lr`, `held_out` in the same file | memory: the count rows | for the run | no |
| Model | `save_private` writes `models/candidates/email_model_v3.joblib` | **disk**: the trained model only | until deleted (see below) | no. Gitignored, never uploaded |
| Reports | `reports/candidates/email_candidates_v3.*`, `reports/privacy/email_v3_privacy_audit.*` | disk | kept | they hold counts and metrics only, no email text (checked by the audit) |
| Logs | the run prints counts and metrics only; per-message failures are counted, and their reasons are never kept | console | the run | no |

No extracted email corpus, plaintext dataset, cache, checkpoint or temporary file is written. The candidate vocabulary is built from **public**
data only, so a word that appears only in the inbox is never counted, even in memory beyond the one message being read.

## Claims and the tests behind them

Synthetic mail only in tests: `tests/test_private_email_pipeline.py` builds a made-up Takeout-style mbox and made-up public corpora in a
temporary folder.

| Claim | Test | Status |
|---|---|---|
| The original archive is never changed | `test_original_mbox_unchanged`; the v3 run and the audit also compare SHA-256 before and after | VERIFIED |
| No email content in logs (stdout, stderr, logging) | `test_no_raw_email_in_logs` | VERIFIED |
| No email content in any database; the pipeline creates none | `test_no_raw_email_in_database` | VERIFIED |
| No network: no network library is imported, and training runs with outbound sockets blocked | `test_no_external_network_transmission`, `test_training_works_offline`; the v3 run blocks sockets and counts attempts | VERIFIED |
| No persistent extracted dataset: only the model file is written | `test_no_persistent_extracted_dataset` | VERIFIED |
| Streaming: one message at a time, the file read incrementally, only integer counts kept | `test_streaming_email_processing` | PARTIAL (see limits) |
| No temporary files left behind | `test_temporary_file_cleanup` | VERIFIED |
| Training works offline | `test_training_works_offline` | VERIFIED |
| No memorisation of unique phrases: canaries repeated 6 times never enter the model, and trained-on and never-seen canaries score identically | `test_model_memorization`; repeated on the real stream by `scripts/privacy_audit_email.py` | VERIFIED on synthetic data; the real result is in the audit |
| No disclosure of names, e-mail addresses, phone numbers, credentials or financial details in the model object | `test_model_sensitive_information_disclosure`; the audit repeats it on the real model | VERIFIED on synthetic data; the real result is in the audit |
| Model file access limited to the owner | `save_private` (icacls on Windows, chmod 600 elsewhere) | PARTIAL: not encrypted |
| Temporary email data released from memory | references dropped after each message | UNVERIFIED: Python cannot prove memory is wiped |

## How the model can still carry information from the inbox

The model is a bag-of-words classifier. Single words and word pairs are weighted by TF-IDF and logistic regression.

- **Its vocabulary has no inbox-only word.** A term is kept only if it appears in at least 5 emails of at least two sources. Every kept term
  therefore also occurs in public data (audit check 2). Numbers are masked before counting, so no phone, account, card or order number can
  become a term.
- **Its numbers are shaped by the inbox.** The IDF values and the weights of common words depend partly on the inbox. Someone with the model
  file could, in principle, learn statistical facts about the inbox: for example, that receipt words pushed scores towards legitimate. This
  is aggregate influence, not stored messages, but it is real.
- **It cannot reproduce a message.** The longest thing it stores is a two-word term.
- **No claim of zero memorisation is made.** The canary tests show that unique strings are not stored and do not change scores. They do not
  prove the model reveals nothing about the inbox.
- **Deleting the .mbox does not remove what the model already learnt.** To withdraw the inbox, delete the export and
  `models/candidates/email_model_v3.joblib` (and any copy), then retrain without it.

## Model files and checkpoints

- No checkpoints are written; training holds everything in memory and saves one final model.
- The model is saved locally with access limited to the current user. It is gitignored and never uploaded or sent to any service.
- It is **not encrypted**. Windows 11 Home has no file encryption (EFS). For encryption at rest, the owner can turn on Device Encryption or
  BitLocker in Windows settings. That is the owner's choice; nothing here changes system settings.
- Model metadata holds only counts, source names and the regularisation value. The vocabulary holds only terms that also occur in public data.

## Deleting the training artefacts

1. Delete `models/candidates/email_model_v3.joblib`, and `models/email_model.joblib` if v3 was ever copied there.
2. Delete `data/raw/email_own/`.
3. The reports keep counts and metrics only and may stay.
4. Retrain without the inbox: `python src/eval_email_v3.py` stops without it, and v2's committed model is unaffected.

## Release rule

The model may be used only if `scripts/privacy_audit_email.py` reports no FAILED exposure check (`reports/privacy/email_v3_privacy_audit.md`)
**and** it passes the project's adoption rule. Weights derived from private mail are never committed to git, because history is permanent and
the repository may later be shared. If v3 is adopted, it stays a local file on the demo laptop, and the committed, reproducible build keeps
v2's email model.

## Limits, stated plainly

- **Streaming is PARTIAL.** Messages are read and turned into counts one at a time, and each text is dropped. The integer counts for all
  inbox emails stay in memory for the run, because evaluation trains several models. No text, header or address is kept.
- **Memory erasure is UNVERIFIED.** Dropping a reference does not wipe memory; the operating system may also page memory to disk.
- **Encryption is not provided** (see above).
- **I never read the mail.** No tool output in this work contains email content; scripts report counts and metrics only. That rests on the
  code paths above and the log tests, not on a further guarantee.
