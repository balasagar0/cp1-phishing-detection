#!/usr/bin/env bash
# Fetches the public LEGITIMATE transactional email material for the email model's v3 attempt (Phase 3.1). All MIT-licensed; a few MB.
#   generated: imnim/multiclass-email-classification (Hugging Face, MIT). GENERATED text, not real messages: labelled synthetic everywhere.
#   templates: ActiveCampaign/postmark-templates and mailgun/transactional-email-templates (GitHub, MIT). Real company template wording,
#              with placeholders; labelled templates, not messages.
# The third part of v3's legitimate data is the team's own inbox export, which a person adds by hand (see src/email_corpora.py, load_own_inbox).
set -eo pipefail
cd "$(dirname "$0")"
mkdir -p data/raw/email_legit/generated data/raw/email_legit/templates
g() { curl -sSL --fail --retry 3 -o "$2" "$1" && echo "ok $2"; }
H=https://huggingface.co/datasets/imnim/multiclass-email-classification/resolve/main
g "$H/email_dataset.json" data/raw/email_legit/generated/email_dataset.json
g "$H/dataset_creation.py" data/raw/email_legit/generated/dataset_creation.py.txt      # how the text was generated (kept as text, never run)
g "$H/README.md" data/raw/email_legit/generated/README.md
g https://codeload.github.com/ActiveCampaign/postmark-templates/zip/refs/heads/main data/raw/email_legit/templates/postmark-templates.zip
g https://codeload.github.com/mailgun/transactional-email-templates/zip/refs/heads/master data/raw/email_legit/templates/mailgun-templates.zip
