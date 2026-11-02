#!/usr/bin/env bash
# Retrains everything (about 15 minutes on one CPU core) and rewrites reports/.
set -e
cd "$(dirname "$0")"
python src/train_email_plain.py 2>&1 | tee reports/log_email_plain.txt
python src/train_email.py       2>&1 | tee reports/log_email.txt
python src/train_sms.py         2>&1 | tee reports/log_sms.txt
python src/train_url.py         2>&1 | tee reports/log_url.txt
python src/train_fusion.py      2>&1 | tee reports/log_fusion.txt
python src/probes.py
python src/eval_window.py     2>&1 | tee reports/log_window.txt
python src/make_report.py
