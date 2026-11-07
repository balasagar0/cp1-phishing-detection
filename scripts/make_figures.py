"""reports/figures/: the figures for the paper, poster and deck (MS-05, R3-23), drawn from reports/ on cp1-final.
  python scripts/make_figures.py        (needs matplotlib: pip install -r requirements-docs.txt)
Each figure is written as PNG at 300 dpi and as SVG, and stays readable in grayscale: the second series is hatched and values are printed.
Colours are the two validated categorical slots (blue, orange) and one sequential blue ramp. reports/figures/README.md names each figure's data.
Simulated results are titled SIMULATED. Nothing is typed: every value comes from the metrics files."""
import json
from pathlib import Path
import matplotlib, matplotlib.ticker
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

ROOT = Path(__file__).resolve().parents[1]; R = ROOT / "reports"; OUT = R / "figures"
jl = lambda p: json.loads(Path(p).read_text(encoding="utf-8"))
BLUE, ORANGE, INK, INK2, GRID, SURF = "#2a78d6", "#eb6834", "#0b0b0b", "#52514e", "#e4e3df", "#ffffff"
SEQ = LinearSegmentedColormap.from_list("seq", ["#cde2fb", "#86b6ef", "#3987e5", "#256abf", "#104281"])
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2,
                     "axes.titlesize": 10, "axes.titleweight": "bold", "axes.spines.top": False, "axes.spines.right": False, "svg.hashsalt": "cp1-final",
                     "figure.facecolor": SURF, "axes.facecolor": SURF, "hatch.linewidth": 0.8})
pct = lambda x: f"{100 * x:.1f}%"
FIGS = []


def save(fig, name, title, data, caption):
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / f"{name}.png", dpi=300, bbox_inches="tight", metadata={"Software": None})
    fig.savefig(OUT / f"{name}.svg", bbox_inches="tight", metadata={"Date": None, "Creator": None})
    plt.close(fig); FIGS.append((name, title, data, caption))


def style(ax, ylabel=None, pct_axis=True, top=1.08):
    ax.grid(axis="y", color=GRID, linewidth=0.6); ax.set_axisbelow(True)
    if pct_axis: ax.set_ylim(0, top); ax.yaxis.set_major_formatter(lambda v, _: f"{round(v * 100, 6):g}%")
    if ylabel: ax.set_ylabel(ylabel)


def label_bars(ax, bars, vals, fmt=pct, inside=False):
    for b, v in zip(bars, vals):
        ax.annotate(fmt(v), (b.get_x() + b.get_width() / 2, b.get_height()), xytext=(0, 2), textcoords="offset points", ha="center", va="bottom", fontsize=7.5, color=INK)


def fig_honest_vs_flattering(E, S, U):
    lo = E["leave_one_corpus_out"]; email_h = sum(v["f1"] for v in lo.values()) / len(lo)
    ch = ["Email", "SMS", "URL"]
    honest = [email_h, S["test_smishing_vs_rest"]["f1"], U["string_model"]["grouped_test"]["f1"]]
    flat = [E["pooled_test"]["f1"], S["test_unwanted_vs_ham"]["f1"], U["feature_benchmark"]["hgb_all_features"]["f1"]]
    fig, ax = plt.subplots(figsize=(6.4, 3.6)); x = range(len(ch)); w = 0.36
    b1 = ax.bar([i - w / 2 - 0.01 for i in x], honest, w, color=BLUE, label="Honest measure (quote this)")
    b2 = ax.bar([i + w / 2 + 0.01 for i in x], flat, w, color=ORANGE, hatch="////", edgecolor=SURF, label="Flattering measure (never alone)")
    label_bars(ax, b1, honest); label_bars(ax, b2, flat)
    ax.set_xticks(list(x)); ax.set_xticklabels(["Email\nhonest: unseen corpus\nflattering: pooled split", "SMS\nhonest: smishing vs rest\nflattering: spam or smishing",
                                               "URL\nhonest: hosts held out\nflattering: random split"], fontsize=7.5)
    style(ax, "F1", top=1.22); ax.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0]); ax.set_title("F1 per detector: the honest measure and the flattering one", loc="left")
    ax.legend(frameon=False, fontsize=7.5, loc="upper left", ncol=2)
    save(fig, "fig1_honest_vs_flattering", "F1 per detector, honest and flattering",
         "`email_metrics.json` (leave_one_corpus_out mean; pooled_test), `sms_metrics.json` (test_smishing_vs_rest; test_unwanted_vs_ham), `url_metrics.json` (string_model.grouped_test; feature_benchmark.hgb_all_features)",
         "Honest: email trained on two corpora and tested on the third (mean of three runs); SMS smishing against everything else; URL with no host in both train and test. Flattering measures are shown only beside them.")


def fig_correlation(CM):
    keys = [("single_channel", "Single\nchannel"), ("parallel_multichannel", "Parallel\nmulti-channel"),
            ("whole_bundle_model", "Whole\nbundle"), ("deployed_engine_60min", "Deployed\n60-min engine")]
    rows = [CM["rows"][k] for k, _ in keys]; labels = [l for _, l in keys]
    fig, axs = plt.subplots(1, 2, figsize=(8.4, 3.4))
    for ax, metric, name in ((axs[0], "f1", "F1"), (axs[1], "false_positive_rate", "False-positive rate")):
        vals = [r[metric] for r in rows]; lo = [r[metric] - r["ci95"][metric][0] for r in rows]; hi = [r["ci95"][metric][1] - r[metric] for r in rows]
        bars = ax.bar(range(4), vals, 0.6, color=[BLUE] * 3 + ["#104281"], yerr=[lo, hi], error_kw={"elinewidth": 0.8, "capsize": 2, "ecolor": INK2})
        bars[3].set_hatch("\\\\\\\\"); bars[3].set_edgecolor(SURF)
        for b, v, h in zip(bars, vals, hi):
            ax.annotate(pct(v), (b.get_x() + b.get_width() / 2, v + h), xytext=(0, 2), textcoords="offset points", ha="center", va="bottom", fontsize=7.5, color=INK)
        ax.set_xticks(range(4)); ax.set_xticklabels(labels, fontsize=7); style(ax, name); ax.set_title(name + " (95% CI)", loc="left", fontsize=9)
    axs[1].set_ylim(0, max(r["ci95"]["false_positive_rate"][1] for r in rows) * 1.35); axs[1].yaxis.set_major_locator(matplotlib.ticker.MultipleLocator(0.05))
    fig.suptitle(f"Correlation against baselines: SIMULATED bundles ({CM['n_bundles']:,} test bundles, alert line {CM['alert_line']:g})", x=0.01, ha="left", fontweight="bold", fontsize=10)
    fig.text(0.01, -0.04, "Single channel: alert if any event scores 0.5 or more. Parallel: the fusion model without link and timing features. "
             "Whole bundle: the correlation model\non every event of the bundle (up to 72 h apart). The hatched bar is what the API does. Events are real held-out messages; the links between them are constructed.", fontsize=6.5, color=INK2)
    fig.tight_layout()
    save(fig, "fig2_correlation_simulated", "Correlation against baselines (SIMULATED)", "`comparison_metrics.json` (rows: precision, recall, f1, false_positive_rate, ci95)",
         "SIMULATED bundles. Single-channel alerting, the fusion model without link and timing features, the correlation model on the whole bundle, and the deployed 60-minute engine. Error bars are 95% bootstrap intervals.")


def fig_confusion(E, S, U):
    lo = E["leave_one_corpus_out"]
    mats = [(f"Email, {c} held out", lo[c]) for c in lo] + [("SMS, smishing vs rest", S["test_smishing_vs_rest"]), ("URL, hosts held out", U["string_model"]["grouped_test"])]
    fig, axs = plt.subplots(1, len(mats), figsize=(11.5, 2.6))
    for ax, (title, m) in zip(axs, mats):
        cm = [[m["tn"], m["fp"]], [m["fn"], m["tp"]]]; rate = [[c / max(sum(r), 1) for c in r] for r in cm]
        ax.imshow(rate, cmap=SEQ, vmin=0, vmax=1)
        for i in range(2):
            for j in range(2):
                ax.text(j, i, f"{cm[i][j]:,}\n{pct(rate[i][j])}", ha="center", va="center", fontsize=7.5, color=SURF if rate[i][j] > 0.55 else INK)
        ax.set_xticks([0, 1]); ax.set_xticklabels(["predicted\nlegitimate", "predicted\nmalicious"], fontsize=7)
        ax.set_yticks([0, 1]); ax.set_yticklabels(["truly\nlegitimate", "truly\nmalicious"], fontsize=7)
        ax.set_title(title, fontsize=8, loc="left"); [s.set_visible(False) for s in ax.spines.values()]
    fig.suptitle("Confusion matrices on the honest measures (count, and share of the true class)", x=0.01, ha="left", fontweight="bold", fontsize=10)
    fig.tight_layout()
    save(fig, "fig3_confusion_matrices", "Confusion matrices, honest measures",
         "`email_metrics.json` (leave_one_corpus_out: tn, fp, fn, tp), `sms_metrics.json` (test_smishing_vs_rest), `url_metrics.json` (string_model.grouped_test)",
         "Each cell shows the count and its share of the true class; darker means a larger share. Email is shown once per held-out corpus.")


def fig_url_tradeoff(U):
    ab = U["string_model"]["ablation"]; steps = [("a_ngrams_only", "N-grams only"), ("b_plus_popularity_flags", "+ popularity\nflags"), ("c_plus_login_training_urls_FINAL", "+ login training\nURLs (final)")]
    login = [ab[k]["false_positive_rate_on_login_urls_of_1000_held_out_popular_domains"] for k, _ in steps]
    rec = [ab[k]["recall_on_bad_urls_hosted_on_top10k_domains"]["recall"] for k, _ in steps]; n = ab[steps[-1][0]]["recall_on_bad_urls_hosted_on_top10k_domains"]["n"]
    fig, axs = plt.subplots(1, 2, figsize=(7.4, 3.2))
    b1 = axs[0].bar(range(3), login, 0.6, color=BLUE); label_bars(axs[0], b1, login)
    b2 = axs[1].bar(range(3), rec, 0.6, color=ORANGE, hatch="////", edgecolor=SURF); label_bars(axs[1], b2, rec)
    for ax, t in ((axs[0], "False alarms on login pages of 1,000\nheld-out popular domains (lower is better)"), (axs[1], f"Recall on bad URLs hosted on\npopular domains, n = {n} (higher is better)")):
        ax.set_xticks(range(3)); ax.set_xticklabels([l for _, l in steps], fontsize=7.5); style(ax); ax.set_title(t, loc="left", fontsize=8.5)
    fig.suptitle("URL detector: the login-page fix and what it costs", x=0.01, ha="left", fontweight="bold", fontsize=10); fig.tight_layout()
    save(fig, "fig4_url_login_tradeoff", "URL login-page trade-off", "`url_metrics.json` (string_model.ablation: a, b, c)",
         "Each step adds to the one before. The final model stops flagging login pages of popular domains, and catches fewer bad URLs hosted on popular domains. Quote both halves.")


def fig_latency(B):
    names = ["/score email", "/score sms", "/score url", "/correlate\nfull case"]; rows = [B["per_channel"]["email"], B["per_channel"]["sms"], B["per_channel"]["url"], B["full_case"]]
    med, p95 = [r["median_ms"] for r in rows], [r["p95_ms"] for r in rows]
    fig, ax = plt.subplots(figsize=(6.4, 3.0)); y = range(4); h = 0.36
    b1 = ax.barh([i - h / 2 - 0.01 for i in y], med, h, color=BLUE, label="Median")
    b2 = ax.barh([i + h / 2 + 0.01 for i in y], p95, h, color=ORANGE, hatch="////", edgecolor=SURF, label="95th percentile")
    for bars, vals in ((b1, med), (b2, p95)):
        for b, v in zip(bars, vals): ax.annotate(f"{v:.0f} ms", (v, b.get_y() + b.get_height() / 2), xytext=(3, 0), textcoords="offset points", va="center", fontsize=7.5, color=INK)
    ax.set_yticks(list(y)); ax.set_yticklabels(names, fontsize=8); ax.invert_yaxis(); ax.set_xlabel("milliseconds")
    ax.grid(axis="x", color=GRID, linewidth=0.6); ax.set_axisbelow(True); ax.set_xlim(0, max(p95) * 1.3)
    ax.set_title(f"Latency over real HTTP, {B['n_per_channel']} requests each, one at a time", loc="left"); ax.legend(frameon=False, fontsize=7.5, loc="upper right")
    fig.text(0.01, -0.09, f"Targets: median 2,000 ms or less per channel; every full case 5,000 ms or less (slowest full case: {B['full_case']['max_ms']:,.0f} ms).\n{B['machine']}.", fontsize=6.5, color=INK2)
    save(fig, "fig5_latency", "Latency over real HTTP", "`benchmark.json` (per_channel, full_case, machine)",
         "Measured on the build laptop, which is not confirmed as the demo laptop. The targets are far off this scale.")


def main():
    E, S, U, CM, B = jl(R / "email_metrics.json"), jl(R / "sms_metrics.json"), jl(R / "url_metrics.json"), jl(R / "comparison_metrics.json"), jl(R / "benchmark.json")
    fig_honest_vs_flattering(E, S, U); fig_correlation(CM); fig_confusion(E, S, U); fig_url_tradeoff(U); fig_latency(B)
    build = jl(R / "final_numbers.json")["build"]
    L = ["# Figures\n", f"Drawn by `scripts/make_figures.py` from the reports of `{build['tag']}` (commit `{build['commit7']}`). Each figure is a PNG at 300 dpi and an SVG. "
         "They read in grayscale: the second series is hatched and every value is printed. Simulated results are titled SIMULATED.\n",
         "| Figure | What it shows | Data | Caption |", "|---|---|---|---|"]
    L += [f"| `{n}.png` / `.svg` | {t} | {d} | {c} |" for n, t, d, c in FIGS]
    (OUT / "README.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {len(FIGS)} figures to reports/figures/")


if __name__ == "__main__":
    main()
