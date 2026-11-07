"""The patent's noisy-OR campaign score (section 7 of the patent specification), as an EVALUATED ALTERNATIVE (Phase 4.3, R3-09). Never wired into the API.
    S = min(1, F * [1 - prod_i (1 - w_c(i) * s_i * exp(-lambda * age_i))])
s_i is event i's detector score, w_c(i) the weight of its channel, age_i its age in minutes at the time the campaign is scored (the newest event has
age 0), lambda the decay rate, and F the product of the cross-channel factor and the sequence factor.
PARAMETERS_FROM_SPEC stays False until the specification is in docs/inputs/: the channel weights, the definitions of the cross-channel and sequence
factors, and the worked example of section 16 must be read from it, not guessed. When it is True, evaluate() applies the score to the same event
groups the deployed engine scores (its 60-minute windows), and chooses lambda, any factor values the spec leaves free, and the alert threshold on
VALIDATION bundles only; eval_comparison.py then reports it on the test bundles beside the other rows."""
import math
import numpy as np

PARAMETERS_FROM_SPEC = False      # stays False: on 7 Nov 2026 the owner decided the patent will be written from this build; the old draft's numbers are generated
SPEC = {"weights": None, "cross_channel_factor": None, "sequence_factor": None, "sequence": None}    # filled from the specification, with the paragraph numbers


def noisy_or(scores, weights, ages, lam, factor=1.0):
    """The core formula. scores, weights, ages: one value per event. Returns S, capped at 1."""
    prod = 1.0
    for s, w, a in zip(scores, weights, ages):
        prod *= 1.0 - min(1.0, max(0.0, w * s * math.exp(-lam * max(0.0, a))))
    return min(1.0, factor * (1.0 - prod))


def campaign_score(events, lam, weights, cross_factor, seq_factor, sequence=None):
    """events: dicts with channel, score, t (minutes). F = cross_factor if two or more channels, times seq_factor if the channels appear in `sequence` order."""
    if not events: return 0.0
    t_now = max(e["t"] for e in events); chans = [e["channel"] for e in sorted(events, key=lambda e: e["t"])]
    F = (cross_factor if len(set(chans)) >= 2 else 1.0) * (seq_factor if sequence and _in_order(chans, sequence) else 1.0)
    return noisy_or([e["score"] for e in events], [weights[e["channel"]] for e in events], [t_now - e["t"] for e in events], lam, F)


def _in_order(chans, sequence):
    it = iter(chans); return all(any(c == s for c in it) for s in sequence)


def evaluate(val, test, time_windows, window):
    """Chooses lambda, the free factor values and the threshold on validation bundles; returns the test risks. Only with PARAMETERS_FROM_SPEC."""
    if not PARAMETERS_FROM_SPEC: raise RuntimeError("the patent specification's parameters are not in place")
    def risks(bundles, lam):
        out = []
        for ev, _, _ in bundles:
            out.append(max(campaign_score([ev[i] for i in g], lam, SPEC["weights"], SPEC["cross_channel_factor"], SPEC["sequence_factor"], SPEC["sequence"]) for g in time_windows(ev, window)))
        return np.array(out)
    yv = np.array([y for _, y, _ in val]); best = None
    for lam in (0.0, 0.001, 0.005, 0.01, 0.02, 0.05):
        rv = risks(val, lam)
        for thr in np.linspace(0.05, 0.95, 19):
            pred = rv >= thr; tp = (pred & (yv == 1)).sum(); fp = (pred & (yv == 0)).sum(); fn = (~pred & (yv == 1)).sum()
            f1 = 2 * tp / max(2 * tp + fp + fn, 1)
            if best is None or f1 > best[0]: best = (f1, lam, float(thr))
    _, lam, thr = best
    return {"risk": risks(test, lam), "threshold": thr, "parameters": {"lambda": lam, **SPEC, "chosen_on": "validation bundles, best F1"}}
