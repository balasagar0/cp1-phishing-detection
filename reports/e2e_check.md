# End-to-end check (R3-03)

Written by `scripts/e2e_check.py` on 2026-11-07T16:32:27+05:30 on `cp1-rc1-2-g50c3228-dirty`, over real HTTP. Demo cases are hand-written, not a test set. Result: **PASS**.

| Step | Result | Detail |
|---|---|---|
| API up, all detectors loaded | pass | channels ['email', 'sms', 'url'], window 60.0 min, correlation trained on simulated bundles |
| console served at / | pass | HTTP 200, script /assets/index-_BF-aL5T.js |
| console presets from the API | pass | 12 presets |
| correlation: TC-06 alerts only as a bundle | pass | bundle risk 0.595, single-channel alert False |
| event store: same risk as /correlate | pass | store 0.595, correlate 0.595 |
| alert raised once, with its reason | pass | 1 new alert(s); linked by ['dom:parcel-redelivery.info'] |
| alert listed, campaign timeline holds the events | pass | 1 open alert(s); timeline 3 events |
| alert acknowledged | pass | ack HTTP 200 |
| control TC-07: three one-event campaigns, no alert | pass | 3 campaigns, 0 alerts, highest 0.451 |
| a call alone: CANNOT_ASSESS, stored, no campaign | pass | status CANNOT_ASSESS |

The console's screens (presets, side-by-side view, replay into the event store) are checked in Chrome and Edge by `scripts/ui_checks.py`.
