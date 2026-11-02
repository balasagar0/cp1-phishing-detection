"""Writes DATA_SOURCES.md (R3-16): every dataset, where it comes from, its licence or terms as checked, when it was downloaded, its SHA-256,
and what uses it.  python scripts/make_data_sources.py
Hashes and dates are read from the files in data/raw (gitignored; fetched by download_data.sh and download_email_extra.sh). The licence notes
record what was checked on 2 Nov 2026: a repository's licence file (GitHub API) and, where one exists, the original publisher's page."""
import hashlib, datetime, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]; RAW = ROOT / "data" / "raw"
SOURCES = [
    ("CEAS_08.csv", "https://raw.githubusercontent.com/PHP4Life/Phishing-Email-Dataset/main/CEAS_08.csv", "Repository has no licence file. Origin: CEAS 2008 spam challenge corpus; its own terms were not found.", "email model (training, leave-one-corpus-out)"),
    ("enron_spam_data.zip", "https://raw.githubusercontent.com/MWiechmann/enron_spam_data/master/enron_spam_data.zip", "Repository licence GPL-3.0. Origin: Enron-Spam (Metsis, Androutsopoulos, Paliouras, 2006).", "email model (unpacked to enron_spam_data.csv)"),
    ("enron_spam_data.csv", "unpacked from enron_spam_data.zip", "as above", "email model"),
    ("fraud_repo.zip", "https://codeload.github.com/smurlafries1/MachineLearningPhishingDetection/zip/refs/heads/main", "Repository has no licence file. It describes the data as the Fraud Email Corpus from Kaggle; that page's terms were not checked.", "email model (fraud_email.csv is taken from it)"),
    ("fraud_email.csv", "unpacked from fraud_repo.zip", "as above", "email model"),
    ("sms.tsv", "https://raw.githubusercontent.com/justmarkham/pycon-2016-tutorial/master/data/sms.tsv", "Repository has no licence file. A copy of the UCI SMS Spam Collection.", "downloaded by download_data.sh but used by no model"),
    ("smish/hcphap_lsdst.csv", "https://raw.githubusercontent.com/hcphap/Smishing-Dataset/main/LSDST-2022.csv.csv", "Repository has no licence file. Same rows and class counts (5,971: 4,844 ham, 638 smishing, 489 spam) as Mishra and Soni, 'SMS Phishing Dataset for Machine Learning and Pattern Recognition', Mendeley Data, DOI 10.17632/f45bkkt8pr.1, licence CC BY 4.0 (checked on the Mendeley page).", "SMS model (training)"),
    ("smish/shaghayegh_combined.csv", "https://raw.githubusercontent.com/shaghayegh-hp/Smishing_Dataset/main/Combined-Labeled-Dataset.csv", "Repository has no licence file; terms unknown.", "SMS external check only (never trained on)"),
    ("url_strings.csv", "https://raw.githubusercontent.com/faizann24/Using-machine-learning-to-detect-malicious-URLs/master/data/data.csv", "Repository has no licence file; terms unknown.", "URL model (training, host-grouped test)"),
    ("url_features_full.csv", "https://raw.githubusercontent.com/GregaVrbancic/Phishing-Dataset/master/dataset_full.csv", "Repository has no licence file. Origin: Vrbancic, Fister and Podgorelec, Data in Brief (2020); its licence was not checked here.", "URL feature benchmark only (offline, not deployed)"),
    ("opendns_top10k.txt", "https://raw.githubusercontent.com/opendns/public-domain-lists/master/opendns-top-domains.txt", "Repository has no licence file; terms unknown.", "URL model (domain-popularity flags, constructed login URLs)"),
    ("email_extra/nazario", "https://monkey.org/~jose/phishing/ (all 17 mailboxes)", "CC-BY-4.0 (LICENSE.txt and README.txt in the same folder). Attribution: Jose Nazario.", "Phase 3.1 email evaluation; email training only if the candidate is adopted"),
    ("email_extra/spamassassin", "https://spamassassin.apache.org/old/publiccorpus/ (easy_ham, easy_ham_2, hard_ham, spam, spam_2)", "readme.html: a corpus for testing spam filters; 'copyright for the text in the messages remains with the original senders'. Do not send these mails into a live mail system.", "Phase 3.1 email evaluation; email training only if the candidate is adopted"),
    ("email_extra/lingspam", "http://www.aueb.gr/users/ion/data/lingspam_public.tar.gz", "readme.txt in the archive: acknowledge the use and origin of the corpus in any published work, and notify Ion Androutsopoulos about it.", "Phase 3.1 email evaluation; email training only if the candidate is adopted"),
]


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()


def main():
    L = ["# Data sources\n", f"Written by `scripts/make_data_sources.py` on {datetime.date.today().isoformat()}. Every dataset the code downloads, with its licence or terms as checked on 2 Nov 2026, "
         "the date it was downloaded on this machine (file time), its SHA-256 and what uses it.\n",
         "**No dataset is in git or redistributed** (`data/` is gitignored). The trained models in `models/` are derived from these datasets: check the terms below before publishing the models or the data. "
         "Datasets marked 'terms unknown' come from repositories with no licence file; the team should check their origin before any publication.\n",
         "Hand-written material (the workbook samples, scenarios, TC-01 to TC-08 and the Indian stories) is the team's own and is never used for training.\n",
         "| File | Source | Licence or terms | Downloaded | Bytes | SHA-256 | Used by |", "|---|---|---|---|---|---|---|"]
    for rel, url, lic, use in SOURCES:
        p = RAW / rel
        files = sorted(x for x in p.rglob("*") if x.is_file()) if p.is_dir() else ([p] if p.exists() else [])
        if not files: L.append(f"| `{rel}` | {url} | {lic} | not downloaded on this machine | – | – | {use} |"); continue
        for i, f in enumerate(files):
            name = f.relative_to(RAW).as_posix()
            when = datetime.datetime.fromtimestamp(f.stat().st_mtime).date().isoformat()
            L.append(f"| `{name}` | {url if i == 0 else '(same source)'} | {lic if i == 0 else '(same)'} | {when} | {f.stat().st_size:,} | `{sha256(f)}` | {use if i == 0 else '(same)'} |")
    L += ["", "Note on dates: unpacked files keep the date stored in their archive, so `enron_spam_data.csv` and `fraud_email.csv` show the archive's date, not the download date.",
          "", "Re-fetch with `bash download_data.sh` and `bash download_email_extra.sh`; `reports/baseline_check.md` records the hashes of the Phase 0 download."]
    (ROOT / "DATA_SOURCES.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote DATA_SOURCES.md: {sum(1 for l in L if l.startswith('| `'))} files")


if __name__ == "__main__":
    main()
