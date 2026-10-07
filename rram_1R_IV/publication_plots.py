"""Publication-style figures (bipolar I-V + endurance/window) for a selected cycle set.

Run after stable50.py / endurance_read_voltages.py:   python publication_plots.py
Makes, for each set (stable50, best50): out/pub_<set>_IV.(png|pdf), out/pub_<set>_endurance.(png|pdf),
out/pub_<set>_combined.(png|pdf).

Read convention (|V| = 100 mV):  SET sweep = + polarity (HRS before SET, LRS after SET),
                                 RESET sweep = - polarity (LRS before RESET, HRS after RESET).
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import LogLocator, NullFormatter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
CC = 110e-6
V_READ = "0.1V"
# I-V display window = sweep range common to both runs (2_21: -3..+4 V, TE_SET: -2.5..+5 V).
# Display only: R and ON/OFF values are read from the full sweeps.
V_NEG_LIMIT, V_POS_LIMIT = -2.5, 4.0
SETS = {  # name: (metrics file, I-V file, index column, x-axis label)
    "stable50": ("stable50_metrics.txt", "stable50_IV_data.txt", "sel_no", "Selected cycle"),
    "best50": ("endurance_read_voltages.txt", "best50_IV_data.txt", "best_no", "Selected cycle"),
}
BLUE, RED, GREY = "#1f5fa8", "#c62828", "#c8c8c8"

plt.rcParams.update({
    "font.family": "DejaVu Serif", "mathtext.fontset": "dejavuserif", "font.size": 12,
    "axes.linewidth": 1.0, "axes.labelsize": 14, "axes.grid": True,
    "grid.linestyle": "--", "grid.color": "#d9d9d9", "grid.linewidth": 0.6,
    "xtick.direction": "in", "ytick.direction": "in", "xtick.top": True, "ytick.right": True,
    "xtick.major.size": 5, "ytick.major.size": 5, "xtick.minor.size": 2.5, "ytick.minor.size": 2.5,
    "xtick.minor.visible": True, "ytick.minor.visible": True,
    "legend.frameon": True, "legend.edgecolor": "#444", "legend.fancybox": False, "legend.fontsize": 10.5,
})


def log_minor(ax):
    ax.yaxis.set_minor_locator(LogLocator(base=10, subs=np.arange(2, 10) * 0.1, numticks=50))
    ax.yaxis.set_minor_formatter(NullFormatter())


def representative(m, idx):
    """Cycle closest to the set median in log R (all four reads) and Vset/Vreset."""
    cols = [f"HRS_pos_{V_READ}", f"LRS_pos_{V_READ}", f"LRS_neg_{V_READ}", f"HRS_neg_{V_READ}"]
    z = np.log10(m[cols])
    if "Vset_V" in m:
        z = pd.concat([z, m[["Vset_V", "Vreset_V"]]], axis=1)
    z = (z - z.median()) / (z.max() - z.min())
    return m.loc[z.abs().sum(axis=1).idxmin(), idx]


def draw_iv(ax, iv, idx, rep, n):
    iv = iv[(iv.V_TE_V >= V_NEG_LIMIT - 1e-3) & (iv.V_TE_V <= V_POS_LIMIT + 1e-3)]
    for _, g in iv.groupby(idx):
        for _, d in g.groupby("sweep"):
            ax.plot(d.V_TE_V, d.I_TE_A.abs(), color=GREY, lw=0.6, alpha=0.8, zorder=1)
    r = iv[iv[idx] == rep]
    ax.plot(r[r.sweep == "SET"].V_TE_V, r[r.sweep == "SET"].I_TE_A.abs(), color=BLUE, lw=2.2, zorder=3, label="SET")
    ax.plot(r[r.sweep == "RESET"].V_TE_V, r[r.sweep == "RESET"].I_TE_A.abs(), color=RED, lw=2.2, zorder=3,
            label="RESET")
    ax.plot([], [], color=GREY, lw=1, label=f"{n} cycles")
    ax.axhline(CC, color="#555", ls="--", lw=1, zorder=2)
    ax.axvline(0, color="#888", lw=0.8, zorder=0)
    ax.set_yscale("log")
    ax.set_ylim(1e-12, 1e-2)
    ax.set_xlim(V_NEG_LIMIT - 0.3, V_POS_LIMIT + 0.3)
    log_minor(ax)
    ax.set_xlabel(r"$V_{TE}$ (V)")
    ax.set_ylabel(r"$|I_{TE}|$ (A)")
    ax.text(0.97, 0.96, "CC = 0.1 mA", transform=ax.transAxes, ha="right", va="top", color="#333", fontsize=11)
    ax.text(0.97, 0.90, "1R, BE grounded", transform=ax.transAxes, ha="right", va="top", color="#555", fontsize=10)
    ax.legend(loc="lower right")


def draw_endurance(ax_r, ax_w, m, idx, xlabel):
    x = m[idx]
    hs, ls_ = m[f"HRS_pos_{V_READ}"], m[f"LRS_pos_{V_READ}"]
    hr, lr = m[f"HRS_neg_{V_READ}"], m[f"LRS_neg_{V_READ}"]
    kw = dict(s=26, linewidths=1.0, zorder=3)
    ax_r.scatter(x, hs, marker="o", facecolors="none", edgecolors=BLUE, label="HRS (SET sweep)", **kw)
    ax_r.scatter(x, ls_, marker="o", color=BLUE, label="LRS (SET sweep)", s=14, zorder=4)  # on top: LRS +/- coincide
    ax_r.scatter(x, hr, marker="s", facecolors="none", edgecolors=RED, label="HRS (RESET sweep)", **kw)
    ax_r.scatter(x, lr, marker="s", color=RED, label="LRS (RESET sweep)", s=34, zorder=3)
    ax_r.set_yscale("log")
    lo = np.nanmin([ls_.min(), lr.min()]); hi = np.nanmax([hs.max(), hr.max()])
    y0, y1 = np.floor(np.log10(lo) - 0.3), np.ceil(np.log10(hi) + 0.3)
    ax_r.set_ylim(10 ** y0, 10 ** y1)
    log_minor(ax_r)
    ax_r.set_ylabel(r"$R$ at $V_{read}$ ($\Omega$)")
    h, l = ax_r.get_legend_handles_labels()
    order = [0, 2, 1, 3]
    ax_r.legend([h[i] for i in order], [l[i] for i in order], ncol=2, fontsize=9.5, loc="lower center",
                bbox_to_anchor=(0.5, 1.01), handletextpad=0.3, columnspacing=1.0,
                title=r"read at $|V|$ = 100 mV", title_fontsize=10)
    ax_r.tick_params(labelbottom=False)

    ax_w.scatter(x, hs / ls_, marker="o", color=BLUE, s=18, label="SET", zorder=3)
    ax_w.scatter(x, hr / lr, marker="s", color=RED, s=18, label="RESET", zorder=3)
    ax_w.axhline(10, color="#999", ls="--", lw=1)
    ax_w.set_yscale("log")
    w = np.r_[hs / ls_, hr / lr]
    ax_w.set_ylim(10 ** min(1, np.floor(np.log10(np.nanmin(w)))) * 0.7, 10 ** (np.ceil(np.log10(np.nanmax(w))) + 1.2))
    log_minor(ax_w)
    ax_w.set_ylabel(r"$R_{HRS}/R_{LRS}$")
    ax_w.set_xlabel(xlabel)
    ax_w.legend(ncol=2, loc="upper center", frameon=False, fontsize=10, handletextpad=0.2)
    ax_w.set_xlim(-1, x.max() + 2)


def endurance_axes(fig, spec):
    sub = spec.subgridspec(2, 1, height_ratios=[2.3, 1], hspace=0.08)
    ax_r = fig.add_subplot(sub[0])
    ax_w = fig.add_subplot(sub[1], sharex=ax_r)
    return ax_r, ax_w


summary = []
for name, (mfile, ivfile, idx, xlabel) in SETS.items():
    m = pd.read_csv(os.path.join(OUT, mfile), sep="\t")
    if "Vset_V" not in m:  # best50: take Vset/Vreset from its own metrics file
        bm = pd.read_csv(os.path.join(OUT, "best50_metrics.txt"), sep="\t")
        m = m.merge(bm[["best_no", "Vset_V", "Vreset_V"]], on="best_no")
    iv = pd.read_csv(os.path.join(OUT, ivfile), sep="\t", comment="#")
    rep = representative(m, idx)
    n = m[idx].nunique()

    fig, ax = plt.subplots(figsize=(6.2, 5.2))
    draw_iv(ax, iv, idx, rep, n)
    ax.set_title("Bipolar I-V (SET/RESET)", fontsize=12, style="italic", color="#333")
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(OUT, f"pub_{name}_IV.{ext}"), dpi=300)
    plt.close(fig)

    fig = plt.figure(figsize=(6.6, 6.0))
    ax_r, ax_w = endurance_axes(fig, fig.add_gridspec(1, 1)[0])
    draw_endurance(ax_r, ax_w, m, idx, xlabel)
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(OUT, f"pub_{name}_endurance.{ext}"), dpi=300)
    plt.close(fig)

    fig = plt.figure(figsize=(13.2, 5.6))
    gs = fig.add_gridspec(1, 2, width_ratios=[1, 1.05], wspace=0.28)
    ax = fig.add_subplot(gs[0])
    draw_iv(ax, iv, idx, rep, n)
    ax_r, ax_w = endurance_axes(fig, gs[1])
    draw_endurance(ax_r, ax_w, m, idx, xlabel)
    med = np.nanmedian(m[f"HRS_pos_{V_READ}"] / m[f"LRS_pos_{V_READ}"])
    fig.text(0.29, -0.01, "Bipolar I-V (SET/RESET)", ha="center", style="italic", color="#3a4a6b", fontsize=12)
    fig.text(0.73, -0.01, f"Endurance / Window (SET: {med:.0f}×)", ha="center", style="italic", color="#3a4a6b",
             fontsize=12)
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(OUT, f"pub_{name}_combined.{ext}"), dpi=300, bbox_inches="tight")
    plt.close(fig)

    r = m[m[idx] == rep].iloc[0]
    summary.append(dict(set=name, rep_index=rep, rep_run=r.run, rep_cycle=r.cycle,
                        median_window_SET=med,
                        median_window_RESET=np.nanmedian(m[f"HRS_neg_{V_READ}"] / m[f"LRS_neg_{V_READ}"])))
print(pd.DataFrame(summary).to_string(index=False, float_format="%.0f"))
