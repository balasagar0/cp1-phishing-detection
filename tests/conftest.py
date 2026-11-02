# smoke_test.py runs at import (it is a script, not pytest tests) and make_synthetic_testcases.py is a generator.
# Keeping them out of collection lets `pytest tests/` run everything else. Run the smoke test on its own: python tests/smoke_test.py
collect_ignore = ["smoke_test.py", "make_synthetic_testcases.py"]
