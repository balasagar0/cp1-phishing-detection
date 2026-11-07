# Privacy audit: email model v3

Written by `scripts/privacy_audit_email.py` on 2026-11-07T11:43:11+05:30, offline. Counts only: no text from the inbox appears here.

| Requirement | Status | Evidence |
|---|---|---|
| memorisation of unique phrases | **FAILED** | canary words in the model: 5; largest score gap between trained-on and never-seen canaries: 2.66e-02; audit model trained on the real stream (4,071 inbox emails) plus 12 canary emails |
| no inbox only terms | **VERIFIED** | model terms: 75,103; terms without public support (5+ emails in a public source): 0 |
| email addresses phone numbers financial details credentials | **FAILED** | e-mail addresses in the model object: 0; numbers of 6+ digits: 0; metadata holds only counts and source names: True; numbers are masked before counting; canary passwords and card numbers absent (check 1) |
| personal names | **PARTIAL** | distinct words in the inbox's names and address local parts: 1,262; of them, single-word model terms: 247. Every model term also occurs in public data (check 2), so these are common words (for example a brand or a common first name), not names learnt from the inbox alone. Their weights are still influenced by the inbox. |
| extraction of unique messages | **FAILED** | longest model term: 2 words (the model cannot hold a sentence); 8-word runs of inbox text found in 33 report and log files: 1 |
| original mbox unchanged | **VERIFIED** | SHA-256 equal before and after the v3 run and this audit: True; test_original_mbox_unchanged |
| no external transmission | **VERIFIED** | outbound attempts during the v3 run: 0, during this audit: 0; test_no_external_network_transmission, test_training_works_offline |
| model file protection | **PARTIAL** | current user only (icacls); not encrypted: Windows 11 Home has no file encryption (EFS). Turning on device encryption or BitLocker is the owner's choice. |
| memory release | **UNVERIFIED** | each email's text is dropped after counting, but Python cannot prove the memory is wiped (garbage collection, OS paging) |
| streaming | **PARTIAL** | each message is read and counted one at a time and its text dropped (test_streaming_email_processing); integer n-gram counts for the inbox stay in memory for the run because the model needs several training passes |

**The model may be used: False.** (It may be used only if no exposure check FAILED.)

Deleting the .mbox does not remove what the model learnt from it: the IDF values and weights of its terms are shaped by the inbox. To withdraw the inbox, delete the export and the model file, and retrain without it.
