#!/usr/bin/env bash
# Fetches the three extra email corpora from their ORIGINAL public sources (Phase 3.1). About 200 MB.
#   Nazario phishing corpus   https://monkey.org/~jose/phishing/          CC-BY-4.0 (attribution: Jose Nazario)
#   SpamAssassin public corpus https://spamassassin.apache.org/old/publiccorpus/   for testing spam filters; copyright stays with the senders
#   Ling-Spam                 http://www.aueb.gr/users/ion/data/          research use (see the README inside the archive)
# Files are kept as downloaded (mbox files and archives); src/email_corpora.py reads them in place, nothing is unpacked.
set -eo pipefail
cd "$(dirname "$0")"
mkdir -p data/raw/email_extra/nazario data/raw/email_extra/spamassassin data/raw/email_extra/lingspam
g() { curl -sSL --fail --retry 3 -o "$2" "$1" && echo "ok $2"; }
N=https://monkey.org/~jose/phishing
for f in README.txt LICENSE.txt phishing0.mbox phishing1.mbox phishing2.mbox phishing3.mbox 20051114.mbox private-phishing4.mbox \
         phishing-2015 phishing-2016 phishing-2017 phishing-2018 phishing-2019 phishing-2020 phishing-2021 phishing-2022 phishing-2023 phishing-2024 phishing-2025; do
  g "$N/$f" "data/raw/email_extra/nazario/$f"
done
S=https://spamassassin.apache.org/old/publiccorpus
g "$S/readme.html" data/raw/email_extra/spamassassin/readme.html
for f in 20030228_easy_ham.tar.bz2 20030228_easy_ham_2.tar.bz2 20030228_hard_ham.tar.bz2 20030228_spam.tar.bz2 20050311_spam_2.tar.bz2; do
  g "$S/$f" "data/raw/email_extra/spamassassin/$f"
done
g http://www.aueb.gr/users/ion/data/lingspam_public.tar.gz data/raw/email_extra/lingspam/lingspam_public.tar.gz
