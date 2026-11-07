# Demo script (CP1 review)

For Viraj and Bala, who run the demo (R3-05). The expected values come from `reports/FINAL_NUMBERS.md` and the build `{{build.tag}}`.
The demo cases are hand-written, not a test set: they show how the system behaves. Never compute a rate from them.

## 1. Before the review

The day before, and again 30 minutes before:

1. Double-click `start_demo.bat` in the project folder. It runs `scripts/preflight.py`, which checks Python and the packages, checks every model
   file against `reports/model_manifest.json`, checks the built console, starts the API without an access log, runs the eight demo cases over
   real HTTP, and checks that nothing needs the network. It prints **GO** or **NO-GO**. On GO the API keeps running and the browser opens
   http://127.0.0.1:8000/.
2. On NO-GO, read the line marked `NO` and go to section 4.
3. Switch Wi-Fi off. The demo needs no network.
4. Keep `reports/FINAL_NUMBERS.md` open in a second window for questions.
5. Check the top bar says **connected** and **Window {{window.minutes}}** minutes.

Who does what: Viraj drives the console. Bala explains the correlation and the event store. Krishna answers on email and SMS, Manoj on testing.

## 2. The order, and what to say

The first three cases make the main point. Run them in this order.

### TC-06: {{demo.TC-06.name}}

- Press **TC-06**, then **Analyze events**.
- Expected: event scores {{demo.TC-06.scores}}, so no event alerts on its own (single-channel view: {{demo.TC-06.alone}}). The bundle risk is **{{demo.TC-06.bundle}}**: {{demo.TC-06.alert}}.
- Say: "Each message alone stays under the alert line of {{alert_line}}. They share one domain and arrive within minutes, so the engine scores
  them together and the bundle alerts. This is the case correlation exists for."
- Say also, if asked how solid it is: "It is one hand-written case, near the line. A retrain on almost the same simulated data moves it from
  {{finalrun.tc06.live}} to {{finalrun.tc06.retrained}}. We kept the shipped model and we report that instability as a limitation."

### TC-07: the same three messages, three days apart

- Press **TC-07**, then **Analyze events**.
- Expected: the same event scores ({{demo.TC-07.scores}}). They fall into three windows, nothing is linked, and the bundle risk is
  **{{demo.TC-07.bundle}}**, the strongest single event: {{demo.TC-07.alert}}.
- Say: "Same messages, but days apart. Events more than {{window.minutes}} minutes apart are never combined, so there is no campaign and no alert."

### TC-05: a colleague shares an article

- Press **TC-05**, then **Analyze events**.
- Expected: event scores {{demo.TC-05.scores}}; bundle risk **{{demo.TC-05.bundle}}**: {{demo.TC-05.alert}}.
- Say: "Three channels, one identity, a few minutes apart, all benign. Linking alone does not raise an alarm: the scores matter."

### Then the rest

| Case | Press | Expected | What to say |
|---|---|---|---|
| TC-04 | TC-04, Analyze | scores {{demo.TC-04.scores}}; bundle {{demo.TC-04.bundle}}, {{demo.TC-04.alert}} | A KYC scam on SMS, link and email, one domain. Every channel already alerts; the bundle shows them as one campaign. |
| TC-08 | TC-08, Analyze | scores {{demo.TC-08.scores}}; bundle {{demo.TC-08.bundle}}, {{demo.TC-08.alert}} | A real-looking courier SMS and email sharing a tracking number. The SMS detector flags it alone. Correlation does not fix a detector false positive: say so. The tracking number is not read as a phone number. |
| TC-01 | TC-01, Analyze | score {{demo.TC-01.scores}}, {{demo.TC-01.alert}} | A phishing email alone. A lone event gets its detector score. |
| TC-02 | TC-02, Analyze | score {{demo.TC-02.scores}}, {{demo.TC-02.alert}} | A smishing SMS alone. |
| TC-03 | TC-03, Analyze | {{demo.TC-03.bundle}} | See below. |

**At TC-03 (a voice call), say:** "This is a call. CP1 has no voice detector: there was no voice data we could use. So the system answers
CANNOT_ASSESS, and the call shows as not assessed. It never says a call is safe. Voice and deepfake detection are planned for Capstone 2."

### The event store (if there is time)

- Load TC-06, type any recipient name (it is stored only as a hash), press **Replay into event store**.
- Expected: one campaign with the three events, one open alert with its reason (which events, which shared token), and an **Acknowledge** button.
- Say: "This is the live path. Each new event regroups the recipient's events into campaigns, using the same window. One alert per campaign,
  raised once. Recipients and identity tokens are stored as HMAC hashes, never in clear."

### The Indian stories (if asked)

IN-01 to IN-04 are hand-written stories in the same console: a KYC freeze, a courier customs fee, a work-from-home task scam, and a legitimate
order that should stay quiet. Expected: IN-01 {{demo.IN-01.alert}}, IN-02 {{demo.IN-02.alert}}, IN-03 {{demo.IN-03.alert}}, IN-04 {{demo.IN-04.alert}} (bundle {{demo.IN-04.bundle}}).

## 3. Numbers to quote, if asked

Quote only these, and only with their condition. Never quote a flattering number alone.

- Email: F1 **{{email.honest.f1}}** on corpora the model never saw (flattering pooled split: {{email.flattering.f1}}).
- SMS: smishing F1 **{{sms.honest.f1}}** (95% CI {{sms.honest.f1_ci}}).
- URL: F1 **{{url.honest.f1}}** with hosts held out. Login-page false alarms {{url.login_fpr.before}} to {{url.login_fpr.after}}, at the cost of recall on bad URLs on popular domains ({{url.popular_recall.before}} to {{url.popular_recall.after}}).
- Correlation, on **simulated** bundles: the {{window.minutes}}-minute engine has F1 {{corr.engine.f1}} and a false-positive rate of {{corr.engine.fpr}},
  against {{corr.single.f1}} and {{corr.single.fpr}} for single-channel alerting. Real bundles have not been collected yet.
- Speed: median {{latency.email.median}} for an email, {{latency.case.median}} for a full case, on the build laptop.

## 4. Fallbacks

| Problem | Do this |
|---|---|
| NO-GO: "venv missing" or a package line | Follow `README.md`, section Install. It needs the internet once; do it the day before. |
| NO-GO: a model hash differs | Someone changed a model file. Run `git checkout -- models` in the project folder, then `start_demo.bat` again. |
| Port 8000 is taken | Close the other program, or run `.venv\Scripts\python.exe scripts\preflight.py --port 8001 --keep-running --open` and use http://127.0.0.1:8001/. |
| The API does not start | Run `.venv\Scripts\python.exe scripts\preflight.py` in a terminal and read the `NO` line. Then try `.venv\Scripts\python.exe -m uvicorn api:app --port 8000 --no-access-log` to see the error. |
| Blank page | Press Ctrl+F5. If it stays blank, open http://127.0.0.1:8000/lite (the one-file console). |
| "not reachable" in the top bar | The API stopped. Start it again and press **Retry**. |
| Nothing works | Show the screenshots in `reports/screenshots/` (taken from this build by `scripts/ui_checks.py`) and the tables in `reports/FINAL_NUMBERS.md`. Say plainly that the live demo failed. |

## 5. Things never to say

- That a call or a video is safe. They are not assessed.
- That the correlation numbers come from real attacks. They come from simulated bundles of real messages.
- Any number from the retired list in `reports/FINAL_NUMBERS.md`, section 9.
- That the risk is a probability. It is a score; the alert line is tied to the simulation's mix.
