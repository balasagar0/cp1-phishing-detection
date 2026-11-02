# Offline check

Written by `scripts/offline_check.py` on 2026-11-02T11:44:43+05:30. Result: **PASS**.

| Check | Result | Detail |
|---|---|---|
| the socket blocker refuses an outbound connection | pass | test attempt recorded: ["create_connection ('example.com', 80)"] |
| public-suffix list is the bundled snapshot | pass | tldextract suffix_list_urls=(), cache_dir=None |
| every demo case and story runs through every route with sockets blocked (8 cases, 4 stories) | pass | 59 requests; failures: none; blocked outbound attempts: none |
| built console and console.html fetch nothing from outside | pass | external fetches: none; console/dist built: True |
| no URL of unknown purpose in the console | pass | URLs that are text only, by kind: {'XML namespace (not fetched)': 5, 'React error-documentation link (text only)': 1, 'this machine': 2, 'preset or sample message text (data, not fetched)': 6} |

## URLs in the console that are text, not fetches

- **XML namespace (not fetched)** (5): `http://www.w3.org/1998/Math/MathML`, `http://www.w3.org/1999/xhtml`, `http://www.w3.org/1999/xlink`, `http://www.w3.org/2000/svg`, `http://www.w3.org/XML/1998/namespace`
- **React error-documentation link (text only)** (1): `https://reactjs.org/docs/error-decoder.html?invariant=`
- **this machine** (2): `http://127.0.0.1:8000`, `http://localhost:8000`
- **preset or sample message text (data, not fetched)** (6): `http://parcel-redelivery.info/confirm`, `http://parcel-redelivery.info/track?id=88213`, `http://sbi-kyc-update.top/verify-now.php`, `https://en.wikipedia.org/wiki/Project_management`, `https://www.fedex.com/fedextrack/?trknbr=123456789012`, `https://www.fedex.com/fedextrack/?trknbr=123456789012.`

This check runs in one process and scans files. A real Wi-Fi-off run on the demo laptop by a person is still needed (R3-06).
