"""No network at runtime (Phase 2.3, R3-06). Nothing may reach the internet while the API or the console runs.
  python scripts/offline_check.py
1. Blocks every outbound socket in this process (only loopback is allowed), then imports the API and runs every demo case and Indian story
   through /score, /correlate, /events, /campaigns and /alerts, and loads /, /lite, /presets and the console's assets. Any blocked attempt fails.
2. Checks the public-suffix list: tldextract must use its bundled snapshot (it fetches a fresh list by default).
3. Scans the built console (console/dist) and console.html for anything a browser would fetch from outside: script and stylesheet links,
   CSS url() and @import, fonts, absolute fetch() or WebSocket targets. URLs that are only text (preset messages, XML namespaces,
   React's error-documentation links) are listed but are not fetches.
Writes reports/offline_check.json and reports/offline_check.md. Exit code 1 on any failure."""
import ipaddress, json, os, re, socket, sys, tempfile, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("CP1_EVENT_DB", str(Path(tempfile.mkdtemp(prefix="cp1_offline_")) / "events.db")); os.environ.setdefault("CP1_HMAC_KEY", "offline-check-key")
ATTEMPTS = []


def _local(host):
    if host in ("localhost", "testserver", "") or host is None: return True
    try: return ipaddress.ip_address(host).is_loopback
    except ValueError: return False


_real_connect, _real_create, _real_gai = socket.socket.connect, socket.create_connection, socket.getaddrinfo
def _connect(self, addr, *a, **k):
    host = addr[0] if isinstance(addr, tuple) else str(addr)
    if not _local(host): ATTEMPTS.append(f"connect {addr}"); raise OSError(f"offline_check: outbound connection to {addr} blocked")
    return _real_connect(self, addr, *a, **k)
def _create(addr, *a, **k):
    if not _local(addr[0]): ATTEMPTS.append(f"create_connection {addr}"); raise OSError(f"offline_check: outbound connection to {addr} blocked")
    return _real_create(addr, *a, **k)
def _gai(host, *a, **k):
    if not _local(host if isinstance(host, str) else None): ATTEMPTS.append(f"getaddrinfo {host}"); raise socket.gaierror(f"offline_check: name lookup for {host} blocked")
    return _real_gai(host, *a, **k)


FETCH = [("script src", re.compile(r"<script[^>]+src=[\"'](https?:)?//", re.I)), ("link href", re.compile(r"<link[^>]+href=[\"'](https?:)?//", re.I)),
         ("img src", re.compile(r"<img[^>]+src=[\"'](https?:)?//", re.I)), ("CSS url()", re.compile(r"url\(\s*[\"']?(https?:)?//", re.I)),
         ("CSS @import", re.compile(r"@import\s+[\"']?(url\()?[\"']?(https?:)?//", re.I)), ("fetch absolute", re.compile(r"fetch\(\s*[\"'`]https?://(?!127\.0\.0\.1|localhost)", re.I)),
         ("WebSocket", re.compile(r"new\s+WebSocket\(\s*[\"'`]wss?://(?!127\.0\.0\.1|localhost)", re.I)), ("font file", re.compile(r"https?://[^\s\"'`)]+\.(woff2?|ttf|otf)\b", re.I)),
         ("Google Fonts or CDN", re.compile(r"https?://(fonts\.googleapis|fonts\.gstatic|cdn\.jsdelivr|unpkg\.com|cdnjs\.cloudflare)", re.I))]
URL = re.compile(r"https?://[^\s\"'`<>)\\]+")
TEXT_ONLY = [(re.compile(r"^https?://www\.w3\.org/"), "XML namespace (not fetched)"), (re.compile(r"^https?://(reactjs\.org|react\.dev)/"), "React error-documentation link (text only)"),
             (re.compile(r"^http://127\.0\.0\.1|^http://localhost"), "this machine")]


def scan_console():
    files = sorted((ROOT / "console" / "dist").rglob("*")) + [ROOT / "console.html"]
    fetches, urls = [], {}
    from demo_cases import CASES, STORIES
    preset_text = json.dumps([CASES, STORIES])
    for p in files:
        if not p.is_file() or p.suffix not in (".html", ".js", ".css", ".json", ".svg"): continue
        t = p.read_text(encoding="utf-8", errors="ignore"); rel = p.relative_to(ROOT).as_posix()
        for name, rx in FETCH:
            for m in rx.finditer(t): fetches.append({"file": rel, "kind": name, "text": t[max(0, m.start() - 20):m.end() + 60]})
        for u in set(URL.findall(t)):
            kind = next((k for rx, k in TEXT_ONLY if rx.search(u)), None) or ("preset or sample message text (data, not fetched)" if u.rstrip(".,") in preset_text or rel == "console.html" else "other text")
            urls.setdefault(kind, set()).add(u)
    return fetches, {k: sorted(v) for k, v in urls.items()}


def main():
    socket.socket.connect, socket.create_connection, socket.getaddrinfo = _connect, _create, _gai
    checks = []
    def check(name, ok, detail): checks.append({"check": name, "ok": bool(ok), "detail": detail})
    try:                                                    # the blocker itself must work, or the checks below prove nothing
        socket.create_connection(("example.com", 80), timeout=3); blocked = False
    except OSError: blocked = bool(ATTEMPTS)
    check("the socket blocker refuses an outbound connection", blocked, f"test attempt recorded: {ATTEMPTS[:1]}"); ATTEMPTS.clear()
    try:
        from fastapi.testclient import TestClient
        import api, url_features
        from demo_cases import CASES, STORIES
        c = TestClient(api.app)
        ext = url_features._EXT
        check("public-suffix list is the bundled snapshot", tuple(ext.suffix_list_urls) == () and not getattr(ext, "cache_dir", None),
              f"tldextract suffix_list_urls={tuple(ext.suffix_list_urls)}, cache_dir={getattr(ext, 'cache_dir', None)}")
        n, bad = 0, []
        for cid, case in {**CASES, **STORIES}.items():
            for e in case["events"]:
                r = c.post("/score", json={"channel": e["channel"], "text": e["text"], "subject": e.get("subject", "")}); n += 1
                if r.status_code not in (200, 501): bad.append(f"{cid} /score {e['channel']} -> {r.status_code}")
            for path, body in (("/correlate", {"events": case["events"]}), ("/events", {"recipient": f"offline-{cid}", "events": case["events"]})):
                r = c.post(path, json=body); n += 1
                if r.status_code != 200: bad.append(f"{cid} {path} -> {r.status_code}")
        for path in ("/health", "/presets", "/campaigns", "/alerts", "/", "/lite"):
            r = c.get(path); n += 1
            if r.status_code != 200: bad.append(f"GET {path} -> {r.status_code}")
        for asset in re.findall(r'(?:src|href)="(/assets/[^"]+)"', c.get("/").text):
            r = c.get(asset); n += 1
            if r.status_code != 200: bad.append(f"GET {asset} -> {r.status_code}")
        check(f"every demo case and story runs through every route with sockets blocked ({len(CASES)} cases, {len(STORIES)} stories)", not bad and not ATTEMPTS,
              f"{n} requests; failures: {bad or 'none'}; blocked outbound attempts: {ATTEMPTS or 'none'}")
    except Exception as ex:
        check("API runs with sockets blocked", False, f"{type(ex).__name__}: {ex}; blocked attempts: {ATTEMPTS}")
    finally:
        socket.socket.connect, socket.create_connection, socket.getaddrinfo = _real_connect, _real_create, _real_gai
    fetches, urls = scan_console()
    check("built console and console.html fetch nothing from outside", not fetches and (ROOT / "console" / "dist" / "index.html").exists(),
          f"external fetches: {fetches or 'none'}; console/dist built: {(ROOT / 'console' / 'dist' / 'index.html').exists()}")
    check("no URL of unknown purpose in the console", not urls.get("other text"), f"URLs that are text only, by kind: { {k: len(v) for k, v in urls.items()} }")
    ok = all(x["ok"] for x in checks)
    doc = {"date": datetime.datetime.now().astimezone().isoformat(timespec="seconds"), "ok": ok, "checks": checks, "text_only_urls": urls}
    (ROOT / "reports" / "offline_check.json").write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    L = ["# Offline check\n", f"Written by `scripts/offline_check.py` on {doc['date']}. Result: **{'PASS' if ok else 'FAIL'}**.\n",
         "| Check | Result | Detail |", "|---|---|---|"] + [f"| {x['check']} | {'pass' if x['ok'] else '**fail**'} | {str(x['detail'])[:600]} |" for x in checks]
    L += ["", "## URLs in the console that are text, not fetches", ""] + [f"- **{k}** ({len(v)}): " + ", ".join(f"`{u}`" for u in v[:12]) + (" ..." if len(v) > 12 else "") for k, v in urls.items()]
    L += ["", "This check runs in one process and scans files. A real Wi-Fi-off run on the demo laptop by a person is still needed (R3-06)."]
    (ROOT / "reports" / "offline_check.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    for x in checks: print(("PASS " if x["ok"] else "FAIL ") + x["check"])
    print("OFFLINE CHECK", "PASSED" if ok else "FAILED"); return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
