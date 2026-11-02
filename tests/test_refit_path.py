"""R2-10 / R3-14: the real-bundle workbook reaches src/refit_fusion.py and its report lands in a reports folder.
Uses only the workbook's EXAMPLE rows (source_type=example, made up for the form), never as data: no bundle is created here.
Run:  python tests/test_refit_path.py      or      pytest tests/test_refit_path.py"""
import subprocess, sys, tempfile, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]


def test_workbook_example_rows_reach_refit_fusion_and_its_report():
    out = Path(tempfile.mkdtemp(prefix="cp1_refit_"))
    p = subprocess.run([sys.executable, str(ROOT / "src" / "refit_fusion.py"), str(ROOT / "testcases" / "review2_testcase_workbook.xlsx"), "--allow-examples",
                        "--reports-dir", str(out), "--models-dir", str(ROOT / "models")], capture_output=True, text=True, timeout=600)
    assert p.returncode == 0, p.stderr[-400:]
    assert (out / "real_bundles_report.md").exists() and (out / "real_bundles_metrics.json").exists(), list(out.iterdir())
    m = json.loads((out / "real_bundles_metrics.json").read_text())
    assert m["window_minutes"] == 60.0 and "H1:" in p.stdout and "time window: 60 minutes" in p.stdout, p.stdout[:400]
    assert not (ROOT / "models" / "fusion_model_real.joblib").exists()          # no --save: nothing is refit


def test_without_examples_the_empty_workbook_is_refused():
    p = subprocess.run([sys.executable, str(ROOT / "src" / "refit_fusion.py"), str(ROOT / "testcases" / "review2_testcase_workbook.xlsx")], capture_output=True, text=True, timeout=300)
    assert p.returncode != 0 and "No usable rows" in (p.stdout + p.stderr), (p.returncode, p.stdout[-300:], p.stderr[-300:])


if __name__ == "__main__":
    ok = True
    for name, fn in sorted((n, f) for n, f in globals().items() if n.startswith("test_") and callable(f)):
        try: fn(); print("PASS", name)
        except Exception as e: ok = False; print("FAIL", name, "-", repr(e)[:400])
    print("ALL PASSED" if ok else "SOME FAILED"); sys.exit(0 if ok else 1)
