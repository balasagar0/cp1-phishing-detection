#!/usr/bin/env bash
# Retrains everything (about 15 minutes on one CPU core) and rewrites reports/.
# On Windows run it from Git Bash. It uses the project's .venv when there is one; set PYTHON to override.
set -eo pipefail
cd "$(dirname "$0")"
if [ -n "${PYTHON:-}" ]; then PY="$PYTHON"
elif [ -x ".venv/Scripts/python.exe" ]; then PY=".venv/Scripts/python.exe"
elif [ -x ".venv/bin/python" ]; then PY=".venv/bin/python"
else PY="python"; fi
echo "using $("$PY" -c 'import sys; print(sys.executable, sys.version.split()[0])')"
"$PY" src/train_email_plain.py 2>&1 | tee reports/log_email_plain.txt
"$PY" src/train_email.py       2>&1 | tee reports/log_email.txt
"$PY" src/train_sms.py         2>&1 | tee reports/log_sms.txt
"$PY" src/train_url.py         2>&1 | tee reports/log_url.txt
"$PY" src/train_fusion.py      2>&1 | tee reports/log_fusion.txt
"$PY" src/probes.py
"$PY" src/eval_window.py     2>&1 | tee reports/log_window.txt
"$PY" src/eval_comparison.py 2>&1 | tee reports/log_comparison.txt
"$PY" src/make_report.py
