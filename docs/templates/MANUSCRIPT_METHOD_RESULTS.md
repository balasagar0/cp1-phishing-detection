# Method and results (manuscript draft, MS-03)

Text for the paper's method and results sections, written from build `{{build.tag}}` (commit `{{build.commit7}}`). The team edits the
wording; the numbers must stay as they are here. Simulated results are called simulated in every sentence that uses them.

## Method

### Overview

The system scores single messages on three channels, email, SMS and URL, and then asks whether several messages to one person belong to
one campaign. Each message becomes an event with a channel, a time, a detector score and identity tokens. A correlation engine groups a
recipient's events into time windows, scores each window with a learned model, and alerts when a window reaches the alert line of
{{alert_line}}. Calls and video are accepted as events but are not scored, because no voice or video detector was trained.

### Data

**Email.** {{email.n}} emails from {{email.n_corpora}} public corpora ({{email.corpora}}), after cleaning and de-duplication. Cleaning drops
scripts and styles with their content, keeps link targets as text, strips the remaining tags and masks numbers and years, which otherwise
identify the corpus rather than the label. The labels are "unwanted or fraudulent" against "legitimate"; they are not strictly phishing.

**SMS.** {{sms.n}} messages in three classes: {{sms.count.ham}} ham, {{sms.count.spam}} spam and {{sms.count.smishing}} smishing. Exact
duplicates and texts with conflicting labels were removed.

**URL.** {{url.n}} URLs on {{url.hosts}} distinct hosts. The training set adds {{url.constructed.train_login_urls}} constructed login URLs on
popular domains, so the model learns that a login path on a well-known domain is not phishing by itself. A separate set of
{{url.constructed.held_out_domain_login_urls}} login URLs on held-out popular domains and {{url.constructed.brand_impersonation_probes}}
brand-impersonation probes is used only for testing.

### Detectors

**Email:** TF-IDF of word 1-2-grams and logistic regression. A term is kept only if it appears in at least five emails of at least two
corpora ({{email.kept_terms}} of {{email.candidate_terms}} candidate terms). This removes corpus fingerprints such as names and mailing-list
words. **SMS:** word and character TF-IDF and multinomial logistic regression over the three classes; the alert score is 1 - P(ham).
**URL:** character n-grams of the canonical URL text, hashed, plus three flags for membership in popularity lists; logistic regression. The
URL detector makes no network request: it never resolves, fetches or looks up a URL.

### Honest evaluation

Each detector is reported on the split that matches how it will be used, beside the easier split that most papers report.

- **Email:** leave-one-corpus-out. The model is trained on two corpora and tested on the third, three times; we report the mean F1. A pooled
  random split is shown beside it as the flattering figure, because each corpus has its own style and a random split rewards learning it.
- **SMS:** smishing against everything else, the class that matters for phishing, with a 95% bootstrap interval. Spam-or-smishing against
  ham is shown as the flattering figure.
- **URL:** an 80/20 split grouped by host, so no host appears in both halves. A random split of a published feature dataset is the
  flattering figure; there, a model can score well by checking whether the URL has a path.

All rates are at the alert line {{alert_line}}. Intervals are bootstrap percentiles.

### Correlation

**Identity tokens.** Registered domains (through the public-suffix list), phone numbers found by phone-shape rules, and an optional sender
identity. Links are cut out before phone numbers are searched, and numbers next to words such as "tracking" or "order" are skipped, so a
parcel number does not link unrelated messages.

**Windows.** Events further apart than {{window.minutes}} minutes are never combined or linked. Each window is described by
{{corr.n_features}} features: the number of events and channels, the highest, mean and lowest score (as logits), the highest score per
channel, which channels are present, whether and how many identity tokens are shared, the share of events that are linked, and the log of
the time span. A gradient-boosting classifier scores the window. The bundle takes its highest window; a window with one event keeps that
event's detector score.

**Simulated bundles.** No public dataset links one attacker's events across channels, so the classifier was trained on simulated bundles.
Each simulated event takes the real held-out score of a randomly drawn real message of the right class and channel; the links and times are
constructed. The mix is: linked attack bundles {{sim.mix.attack_linked}}, single attack events {{sim.mix.attack_single}}, mixed unlinked
{{sim.mix.mixed_unlinked}}, linked benign bundles {{sim.mix.benign_linked}} and unlinked benign bundles {{sim.mix.benign_unlinked}}. Linked
attacks have 2-3 events on different channels with a shared identity and short gaps; linked benign bundles have the same shape with longer
gaps; unlinked bundles spread events over three days and occasionally share an identity by chance. A bundle is labelled malicious if any
event is malicious. We used {{corr.n_train}} bundles to train, {{corr.n_val}} to tune and {{corr.n_test}} to test.

**Baselines.** On the same simulated test bundles we compare: single-channel alerting (alert if any event reaches the line); a parallel
multi-channel model (the same classifier trained without the {{corr.n_link_features}} link and timing features); the classifier on the whole
bundle with no window; and the deployed engine with {{window.minutes}}-minute windows.

### Event store

A live path keeps each recipient's events in SQLite. The recipient and every identity token are stored as HMAC-SHA256 hashes, and message text
is not stored by default. Each new event regroups the recipient's events into campaigns, using the same windows, and the first time a campaign
reaches the alert line it raises one alert with its reason.

## Results

### Detectors

{{block:detectors}}

The gap between the honest and the flattering figures is largest for email: {{email.honest.f1}} on unseen corpora against
{{email.flattering.f1}} on a pooled split. On unseen corpora the false-positive rate ranges from {{email.honest.fpr_range}} and recall from
{{email.honest.recall_range}}, while the ranking quality stays fairly high (ROC-AUC {{email.honest.auc_range}}): the threshold does not
transfer between sources. On {{email.realmail.n}} real legitimate emails from one consenting user's own mailbox (processed on that user's laptop and
never stored or shared), the email model raised a false alarm on {{email.realmail.fpr}}.

For URLs, training on constructed login URLs cut false alarms on the login pages of {{url.constructed.held_out_domain_login_urls}} URLs on
held-out popular domains from {{url.login_fpr.before}} to {{url.login_fpr.after}}. The cost is recall on bad URLs hosted on popular domains,
which fell from {{url.popular_recall.before}} to {{url.popular_recall.after}} (n = {{url.popular_recall.n}}).

For SMS, the smishing class has {{sms.smishing_support}} test messages, so the interval on its F1 is wide ({{sms.honest.f1_ci}}).

### Correlation (simulated bundles)

{{block:corr}}

On simulated bundles, the deployed engine beats single-channel alerting by a little: F1 {{corr.engine.f1}} against {{corr.single.f1}}, and a
false-positive rate of {{corr.engine.fpr}} against {{corr.single.fpr}}. The model without a window does better on this simulation
(F1 {{corr.nowindow.f1}}, false-positive rate {{corr.nowindow.fpr}}) because the simulation's unlinked bundles are labelled as a whole, so
pooling events days apart helps there; the window stops that pooling. We keep the window because, in real mail, messages days apart are
rarely one campaign, and we treat the windowed row as the cautious estimate.

Most of the gain comes from combining scores, not from link and timing evidence: the ROC-AUC goes from {{corr.auc.single}} (the highest
single score) to {{corr.auc.nocorr}} (the learned combination without link and timing features) to {{corr.auc.fusion}} (with them). Only
{{corr.hard.n}} simulated linked attacks ({{corr.hard.share}}) have every event below the line; the deployed engine flags
{{corr.engine.hard_flagged}} of them. {{corr.fit60}} of simulated linked attack bundles fit inside one window.

### Stability

A full retrain of the same recipe on this build, where only the email text cleaner had changed, gave an almost identical simulated result
(F1 {{finalrun.sim_f1.live}} before and {{finalrun.sim_f1.retrained}} after) but moved one hand-written borderline campaign from
{{finalrun.tc06.live}} to {{finalrun.tc06.retrained}}, below the line. The correlation model's verdict on borderline bundles is therefore not
stable under retraining, and simulated metrics do not show it.

### Speed

Over real HTTP on a laptop ({{latency.machine}}), the median time to score one email was {{latency.email.median}}, one SMS
{{latency.sms.median}} and one URL {{latency.url.median}}; a full multi-event case took {{latency.case.median}} at the median.

## Limitations

The correlation results are simulated: the events are real, the campaigns are not, and the alert line is tied to the simulation's mix. The
risk is a score, not a calibrated probability. The email labels mix spam and fraud with phishing, and the model does not transfer well across
sources. The URL detector trades recall on popular domains for fewer false alarms on login pages. The SMS smishing class is small. A detector
false positive stays a false positive after correlation. Voice and video are not assessed. Real coordinated bundles, collected with consent,
are needed to test the central claim.
