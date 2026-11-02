"""URL helpers shared by training and inference: canonicalisation, registered-domain popularity features, test-URL generators."""
import re
import numpy as np
from scipy import sparse
import tldextract

_EXT = tldextract.TLDExtract(suffix_list_urls=(), cache_dir=None)   # bundled public-suffix snapshot, no network
BUCKETS = (100, 1000, 10000)                                          # popularity-rank cut-offs


def canon(u):
    """Strip scheme, leading www., trailing slash (the raw data has 'good' URLs without scheme/www and always with '/')."""
    u = str(u).strip().lower()
    u = re.sub(r"^[a-z][a-z0-9+.\-]*://", "", u)
    u = re.sub(r"^www\d?\.", "", u)
    return u.rstrip("/")


def host_of(c):
    return re.sub(r":\d+$", "", re.split(r"[/?#]", c, maxsplit=1)[0].split("@")[-1])


_RD = {}
def reg_domain(host):
    if host not in _RD:
        r = _EXT(host)
        _RD[host] = getattr(r, "top_domain_under_public_suffix", None) or getattr(r, "registered_domain", "") or host
    return _RD[host]


def load_rank_map(path):
    rm = {}
    for line in open(path):
        d = line.strip().lower()
        if d and not d.startswith("#"):
            rm.setdefault(reg_domain(d), len(rm) + 1)
    return rm


def rank_of(host, rm):
    return rm.get(reg_domain(host), 10 ** 9)


def rep_matrix(hosts, rm):
    r = np.array([rank_of(h, rm) for h in hosts])
    return sparse.csr_matrix(np.stack([(r <= b) for b in BUCKETS], 1).astype(np.float32))


# ---- constructed test URLs (NOT real-world samples; used only for the before/after checks) ----
LOGIN_PATHS = ["/login", "/signin", "/sign-in", "/account/login", "/accounts/login", "/user/login", "/auth/login", "/my-account",
               "/secure/login", "/login.html", "/account/signin?next=/home", "/signin?returnUrl=/", "/customer/account/login",
               "/session/new", "/account/verify", "/verify-account", "/update-billing", "/password-reset"]
PREFIX = ["", "", "www.", "login.", "accounts.", "secure.", "my.", "id.", "auth."]
EVIL_TLDS = ["xyz", "top", "ml", "tk", "ga", "cf", "gq", "club", "online", "site", "info", "ru", "cn", "icu", "buzz"]
EVIL_WORDS = ["verify", "account", "secure", "update", "support", "service", "login", "billing", "kyc", "alert", "confirm", "help"]
ATTACK_PATHS = ["/login", "/signin", "/verify", "/update.php", "/account/confirm", "/secure/login.php", "/index.php?id=3", "/verify-now.php"]


def make_login_urls(domains, n, rng):
    return [canon(PREFIX[rng.integers(len(PREFIX))] + d + LOGIN_PATHS[rng.integers(len(LOGIN_PATHS))]) for d in domains for _ in range(n)]


def make_brand_probes(brands, n, rng):
    out = []
    for _ in range(n):
        b = brands[rng.integers(len(brands))]; w = lambda: EVIL_WORDS[rng.integers(len(EVIL_WORDS))]
        t = EVIL_TLDS[rng.integers(len(EVIL_TLDS))]; p = ATTACK_PATHS[rng.integers(len(ATTACK_PATHS))]
        k = rng.integers(4)
        u = (f"{b}-{w()}.{w()}-{w()}.{t}{p}" if k == 0 else f"{b}.com.{w()}-{w()}.{t}{p}" if k == 1
             else f"secure.{b}.com.{w()}.{t}{p}" if k == 2 else f"{w()}-{b}.{t}{p}")
        out.append(canon(u))
    return out
