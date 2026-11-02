"""Local API for the React console:  uvicorn api:app --port 8000
POST /score        {"channel":"email|sms|url","text":"...","subject":"(email only, optional)"}
POST /score/batch  {"items":[{...},{...}]}
POST /correlate    {"events":[{"channel","text","subject","identity","time"},...], "window_minutes": 60}   (window optional; events further apart are not combined or linked)"""
import sys, math
from pathlib import Path
from typing import List, Optional
sys.path.insert(0, str(Path(__file__).parent / "src"))
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from predict import Detectors, extract_ids
from fusion import Fusion
from datetime import datetime

app = FastAPI(title="CP1 per-channel phishing detectors", version="0.1")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])  # local demo only
D = Detectors()
_real = Path(__file__).parent / "models" / "fusion_model_real.joblib"   # written by src/refit_fusion.py --save
F = Fusion(_real if _real.exists() else Path(__file__).parent / "models" / "fusion_model.joblib")


class Item(BaseModel):
    channel: str
    text: str = Field(min_length=1)
    subject: Optional[str] = ""


class Event(BaseModel):
    channel: str
    text: str = Field(min_length=1)
    subject: Optional[str] = ""
    identity: Optional[str] = ""          # sender number / address / domain, if known
    time: Optional[str] = None            # ISO timestamp, or minutes as a number string; only differences matter


class Bundle(BaseModel):
    events: List[Event]
    window_minutes: Optional[float] = Field(default=None, gt=0, le=10080)   # None = the model's window (60 minutes unless a refit stored another)


def _minutes(t, i):
    bad = HTTPException(status_code=422, detail=f"event {i}: 'time' must be a number of minutes or an ISO timestamp, got '{t}'")
    if t in (None, ""): return float(i)
    try: v = float(t)
    except ValueError:
        try: v = datetime.fromisoformat(str(t).replace("Z", "+00:00")).timestamp() / 60.0
        except ValueError: raise bad
    if not math.isfinite(v): raise bad
    return v


class Batch(BaseModel):
    items: List[Item]


def _run(it: Item):
    try:
        return D.score(it.channel.lower(), it.text, it.subject or "")
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))


@app.get("/health")
def health():
    return {"status": "ok", "channels": ["email", "sms", "url"], "not_trained": ["voice", "video"], "fusion_trained_on": F.trained_on, "window_minutes": F.window}


@app.post("/score")
def score(it: Item):
    return _run(it)


@app.post("/score/batch")
def score_batch(b: Batch):
    return [_run(i) for i in b.items]


@app.post("/correlate")
def correlate(b: Bundle):
    """Scores every event with its channel detector, then scores the bundle with the correlation model.
    Events further apart than the time window are not combined or linked; each window is scored on its own and the bundle takes the highest."""
    if not b.events: raise HTTPException(status_code=422, detail="no events")
    out, ev = [], []
    for i, e in enumerate(b.events):
        try: r = D.score(e.channel.lower(), e.text, e.subject or "")
        except NotImplementedError as ex: raise HTTPException(status_code=501, detail=str(ex))
        ids = extract_ids(e.channel.lower(), e.text, e.identity or "")
        t = _minutes(e.time, i)
        out.append({**r, "identity_tokens": ids, "t_minutes": t}); ev.append({"channel": r["channel"], "score": r["score"], "ids": ids, "t": t})
    f = F.risk(ev, b.window_minutes)
    win = f["window_events"]
    for i, o in enumerate(out): o["in_window"] = i in win
    cnt = {}
    for i in win:
        for tok in set(ev[i]["ids"]): cnt[tok] = cnt.get(tok, 0) + 1
    ts = [e["t"] for e in ev]; tw = [ev[i]["t"] for i in win]
    return {"events": out, "single_channel_alert": any(e["score"] >= D.threshold for e in ev), "bundle_risk": f["risk"],
            "bundle_risk_without_correlation": f["risk_without_correlation"], "alert_threshold": 0.5,
            "bundle_label": "elevated risk" if f["risk"] >= 0.5 else "low risk",
            "shared_identity_tokens": sorted(t for t, c in cnt.items() if c >= 2), "time_span_minutes": round(max(ts) - min(ts), 2),
            "window_minutes": f["window_minutes"], "n_windows": f["n_windows"], "window_event_indices": win,
            "window_time_span_minutes": round(max(tw) - min(tw), 2),
            "features": f["features"], "fusion_trained_on": F.trained_on, "note": f"correlation model trained on {F.trained_on}"}
