# Latency benchmark

Written by `scripts/benchmark.py` on 2026-11-07T16:42:30+05:30 on `cp1-rc1-2-g50c3228-dirty`. real HTTP to uvicorn on http://127.0.0.1:51908, requests one at a time after a warm-up.

Machine: AMD Ryzen 7 5800HS with Radeon Graphics (16 logical CPUs), 15.4 GB RAM, Windows-11-10.0.26200-SP0, Python 3.13.0. **not confirmed: Viraj confirms whether this is the demo laptop, or re-runs this script on it (R3-10).**

| Request | n | Median | 95th percentile | Max | Target | Met |
|---|---|---|---|---|---|---|
| /score email | 100 | 23 ms | 39 ms | 138 ms | NFR-01: median 2 s or less | yes |
| /score sms | 100 | 12 ms | 14 ms | 16 ms | NFR-01: median 2 s or less | yes |
| /score url | 100 | 6 ms | 8 ms | 10 ms | NFR-01: median 2 s or less | yes |
| /correlate full case (TC-01 to TC-08 in turn) | 100 | 67 ms | 89 ms | 1970 ms | NFR-02: every case 5 s or less | yes |

Server start-up (models loaded, /health answering): 8.2 s.
