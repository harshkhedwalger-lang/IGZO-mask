"""Device 5_5 (2026-09-04): forming + 50 consecutive SET/RESET cycles, CC = 0.1 mA, publication-style plots.

Raw (raw_5_5/): ID1 = empty (timestamp only), ID2 = forming 0 -> 10 V, ID3 = SET 0 -> 3 V, ID4 = RESET 0 -> -2 V,
0.05 V steps, 50 loops each; SET loop n is followed by RESET loop n (one cycle).
All 50 cycles are shown, in measurement order (no selection).

Outputs (out_5_5/): cycle_metrics.txt, IV_all_cycles.txt, forming.(png|pdf), IV.(png|pdf), endurance.(png|pdf),
combined.(png|pdf)
Run:  python plot_5_5.py
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import LogLocator, NullFormatter

HERE = os.path.dirname(os.path.abspath(__file__))
RAW, OUT = os.path.join(HERE, "raw_5_5"), os.path.join(HERE, "out_5_5")
os.makedirs(OUT, exist_ok=True)
CC = 110e-6          # measured compliance plateau (nominal 0.1 mA)
V_READ, V_TOL = 0.1, 0.01
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


def load(fname):
    d = pd.read_csv(os.path.join(RAW, fname), sep="\t", skiprows=[1, 2], na_values=["--"])
    d = d.rename(columns=lambda c: c.replace("_set", "").replace("_reset", "").replace("_forming", ""))
    return d.rename(columns={"Loop2 Index": "loop", "SMU_TE Voltage": "V", "SMU_TE Current": "I"})


def read_R(v, i, compliance_limited=False):
    """|V/I| at the point closest to |V| = V_READ. On the SET sweep the SMU limit is active, so a
    current at the limit only bounds R (R <= V/CC) and is returned as NaN."""
    k = np.argmin(np.abs(np.abs(v) - V_READ))
    if abs(abs(v[k]) - V_READ) > V_TOL or i[k] == 0:
        return np.nan
    if compliance_limited and abs(i[k]) >= 0.95 * CC:
        return np.nan
    return abs(v[k] / i[k])


def log_minor(ax):
    ax.yaxis.set_minor_locator(LogLocator(base=10, subs=np.arange(2, 10) * 0.1, numticks=50))
    ax.yaxis.set_minor_formatter(NullFormatter())


# ---- metrics -----------------------------------------------------------------------------
S, R = load("5_5_ID3_set.txt"), load("5_5_ID4_reset.txt")
rows, parts = [], []
for n in sorted(set(S.loop) & set(R.loop)):
    s, r = S[S.loop == n], R[R.loop == n]
    vs, is_, vr, ir = s.V.values, s.I.values, r.V.values, r.I.values
    ks, kr = np.argmax(vs), np.argmin(vr)
    hit = np.where(is_[:ks + 1] >= 0.9 * CC)[0]
    kk = np.argmax(np.abs(ir[:kr + 1]))
    m = {"cycle": n, "Vset_V": vs[hit[0]] if len(hit) else np.nan,
         "V_at_Imax_reset_V": vr[kk], "Imax_reset_A": abs(ir[kk]),
         "HRS_SET_ohm": read_R(vs[:ks + 1], is_[:ks + 1], compliance_limited=True),
         "LRS_SET_ohm": read_R(vs[ks:], is_[ks:], compliance_limited=True),
         "LRS_RESET_ohm": read_R(vr[:kr + 1], ir[:kr + 1]),
         "HRS_RESET_ohm": read_R(vr[kr:], ir[kr:])}
    m["ON_OFF_SET"] = m["HRS_SET_ohm"] / m["LRS_SET_ohm"]
    m["ON_OFF_RESET"] = m["HRS_RESET_ohm"] / m["LRS_RESET_ohm"]
    # abrupt RESET = current peaks before the end of the sweep; gradual = largest current at -2 V
    m["reset_type"] = "gradual" if abs(vr[kk] - vr.min()) < 0.01 else "abrupt"
    rows.append(m)
    for sweep, d in (("SET", s), ("RESET", r)):
        parts.append(pd.DataFrame({"cycle": n, "sweep": sweep, "V_TE_V": d.V.values, "I_TE_A": d.I.values}))
M = pd.DataFrame(rows)
IV = pd.concat(parts, ignore_index=True)
M.to_csv(os.path.join(OUT, "cycle_metrics.txt"), sep="\t", index=False, float_format="%.6g", na_rep="NaN")
with open(os.path.join(OUT, "IV_all_cycles.txt"), "w") as fh:
    fh.write("# Device 5_5, 50 consecutive DC cycles, CC = 0.1 mA (SMU limit 110 uA), TE biased, BE grounded\n")
    IV.to_csv(fh, sep="\t", index=False, float_format="%.6e")

# representative cycle: complete reads, closest to the median in log R and Vset (cycle 1 = first after forming)
full = M[M.cycle > 1].dropna(subset=["HRS_SET_ohm", "LRS_SET_ohm", "LRS_RESET_ohm", "HRS_RESET_ohm"])
z = np.log10(full[["HRS_SET_ohm", "LRS_SET_ohm", "LRS_RESET_ohm", "HRS_RESET_ohm"]]).join(full.Vset_V)
z = (z - z.median()) / (z.max() - z.min())
REP = int(full.loc[z.abs().sum(axis=1).idxmin(), "cycle"])


# ---- figure pieces -----------------------------------------------------------------------
def draw_forming(ax):
    F = load("5_5_ID2_forming.txt")
    ax.plot(F.V, F.I.abs(), color="#333", lw=2)
    kf = np.where(F.I.values >= 0.9 * CC)[0][0]
    ax.annotate(f"$V_{{form}}$ ≈ {F.V.values[kf]:.1f} V", xy=(F.V.values[kf], CC), xytext=(F.V.values[kf] + 0.8, 3e-7),
                arrowprops=dict(arrowstyle="->", color="#333"), fontsize=12)
    ax.axhline(CC, color="#555", ls="--", lw=1)
    ax.set_yscale("log"); ax.set_ylim(1e-12, 1e-3); log_minor(ax)
    ax.set_xlabel(r"$V_{TE}$ (V)"); ax.set_ylabel(r"$|I_{TE}|$ (A)")
    ax.text(0.97, 0.96, "CC = 0.1 mA", transform=ax.transAxes, ha="right", va="top", fontsize=11, color="#333")


def draw_iv(ax):
    for (_, _), d in IV.groupby(["cycle", "sweep"]):
        ax.plot(d.V_TE_V, d.I_TE_A.abs(), color=GREY, lw=0.6, alpha=0.8, zorder=1)
    r = IV[IV.cycle == REP]
    for sweep, col in (("SET", BLUE), ("RESET", RED)):
        d = r[r.sweep == sweep]
        ax.plot(d.V_TE_V, d.I_TE_A.abs(), color=col, lw=2.2, zorder=3, label=f"{sweep} (cycle {REP})")
    ax.plot([], [], color=GREY, lw=1, label=f"{M.cycle.nunique()} cycles")
    ax.axhline(CC, color="#555", ls="--", lw=1, zorder=2)
    ax.axvline(0, color="#888", lw=0.8, zorder=0)
    ax.set_yscale("log"); ax.set_ylim(1e-10, 1e-2); log_minor(ax)
    ax.set_xlim(IV.V_TE_V.min() - 0.2, IV.V_TE_V.max() + 0.2)
    ax.set_xlabel(r"$V_{TE}$ (V)"); ax.set_ylabel(r"$|I_{TE}|$ (A)")
    ax.text(0.97, 0.96, "CC = 0.1 mA", transform=ax.transAxes, ha="right", va="top", color="#333", fontsize=11)
    ax.text(0.97, 0.90, "1R, BE grounded", transform=ax.transAxes, ha="right", va="top", color="#555", fontsize=10)
    ax.legend(loc="lower right")


def draw_endurance(ax_r, ax_w):
    x = M.cycle
    kw = dict(s=26, linewidths=1.0, zorder=3)
    ax_r.scatter(x, M.HRS_SET_ohm, marker="o", facecolors="none", edgecolors=BLUE, label="HRS (SET sweep)", **kw)
    ax_r.scatter(x, M.LRS_SET_ohm, marker="o", color=BLUE, label="LRS (SET sweep)", s=14, zorder=4)
    ax_r.scatter(x, M.HRS_RESET_ohm, marker="s", facecolors="none", edgecolors=RED, label="HRS (RESET sweep)", **kw)
    ax_r.scatter(x, M.LRS_RESET_ohm, marker="s", color=RED, label="LRS (RESET sweep)", s=34, zorder=3)
    ax_r.set_yscale("log"); ax_r.set_ylim(1e2, 1e7); log_minor(ax_r)
    ax_r.set_ylabel(r"$R$ at $V_{read}$ ($\Omega$)")
    h, l = ax_r.get_legend_handles_labels()
    ax_r.legend([h[i] for i in (0, 2, 1, 3)], [l[i] for i in (0, 2, 1, 3)], ncol=2, fontsize=9.5,
                loc="lower center", bbox_to_anchor=(0.5, 1.01), handletextpad=0.3, columnspacing=1.0,
                title=r"read at $|V|$ = 100 mV", title_fontsize=10)
    ax_r.tick_params(labelbottom=False)
    ax_w.scatter(x, M.ON_OFF_SET, marker="o", color=BLUE, s=18, label="SET", zorder=3)
    ax_w.scatter(x, M.ON_OFF_RESET, marker="s", color=RED, s=18, label="RESET", zorder=3)
    ax_w.axhline(10, color="#999", ls="--", lw=1)
    ax_w.set_yscale("log"); ax_w.set_ylim(0.7, 3e3); log_minor(ax_w)
    ax_w.set_ylabel(r"$R_{HRS}/R_{LRS}$"); ax_w.set_xlabel("Cycle")
    ax_w.legend(ncol=2, loc="upper center", frameon=False, fontsize=10, handletextpad=0.2)
    ax_w.set_xlim(-1, x.max() + 2)


def endurance_axes(fig, spec):
    sub = spec.subgridspec(2, 1, height_ratios=[2.3, 1], hspace=0.08)
    ax_r = fig.add_subplot(sub[0])
    return ax_r, fig.add_subplot(sub[1], sharex=ax_r)


def save(fig, name, **kw):
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(OUT, f"{name}.{ext}"), dpi=300, **kw)
    plt.close(fig)


fig, ax = plt.subplots(figsize=(6.2, 5.0)); draw_forming(ax)
ax.set_title("Forming (device 5_5)", fontsize=12, style="italic", color="#333"); fig.tight_layout(); save(fig, "forming")

fig, ax = plt.subplots(figsize=(6.2, 5.2)); draw_iv(ax)
ax.set_title("Bipolar I-V (SET/RESET)", fontsize=12, style="italic", color="#333"); fig.tight_layout(); save(fig, "IV")

fig = plt.figure(figsize=(6.6, 6.0)); draw_endurance(*endurance_axes(fig, fig.add_gridspec(1, 1)[0]))
fig.tight_layout(); save(fig, "endurance")

med_set, med_reset = np.nanmedian(M.ON_OFF_SET), np.nanmedian(M.ON_OFF_RESET)
fig = plt.figure(figsize=(13.2, 5.6))
gs = fig.add_gridspec(1, 2, width_ratios=[1, 1.05], wspace=0.28)
draw_iv(fig.add_subplot(gs[0]))
draw_endurance(*endurance_axes(fig, gs[1]))
fig.text(0.29, -0.01, "Bipolar I-V (SET/RESET)", ha="center", style="italic", color="#3a4a6b", fontsize=12)
fig.text(0.73, -0.01, f"Endurance / Window (SET: {med_set:.0f}×, RESET: {med_reset:.0f}×)", ha="center",
         style="italic", color="#3a4a6b", fontsize=12)
save(fig, "combined", bbox_inches="tight")

# ---- console summary -----------------------------------------------------------------------
print("representative cycle:", REP)
print(M[["Vset_V", "Imax_reset_A", "HRS_SET_ohm", "LRS_SET_ohm", "LRS_RESET_ohm", "HRS_RESET_ohm",
         "ON_OFF_SET", "ON_OFF_RESET"]].describe().loc[["count", "mean", "std", "min", "50%", "max"]]
      .to_string(float_format="%.4g"))
print("reset type:", M.reset_type.value_counts().to_dict())
print("SET-sweep LRS at compliance (R <= 0.91 kOhm, not plotted): cycles",
      M.cycle[M.LRS_SET_ohm.isna()].tolist())
print("cycles with ON/OFF < 10 (SET / RESET):", int((M.ON_OFF_SET < 10).sum()), "/", int((M.ON_OFF_RESET < 10).sum()))
