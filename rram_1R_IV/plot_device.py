"""Per-device plots: forming + all consecutive SET/RESET cycles, publication style.

Each device folder raw_<dev>/ holds <dev>_ID2_forming.txt, <dev>_ID3_set.txt, <dev>_ID4_reset.txt
(ID1 is an empty timestamp file). SET loop n is followed by RESET loop n (one cycle). All cycles are shown in
measurement order, no selection.

Outputs (out_<dev>/): cycle_metrics.txt, IV_all_cycles.txt, forming / IV / endurance / combined (.png + .pdf)
Run:  python plot_device.py 5_5      python plot_device.py 8_81
"""
import os
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import LogLocator, NullFormatter

# cc: measured SMU compliance plateau; cc_label: nominal setting; formed: False if the forming sweep shows no
# abrupt forming event (device conductive from the first point); v_pos_max: I-V display limit (None = full sweep)
DEVICES = {
    "5_5": dict(cc=110e-6, cc_label="0.1 mA", formed=True, v_pos_max=None),
    "8_81": dict(cc=530e-6, cc_label="0.5 mA", formed=False, v_pos_max=2.0),
}
DEV = sys.argv[1] if len(sys.argv) > 1 else "5_5"
CFG = DEVICES[DEV]
HERE = os.path.dirname(os.path.abspath(__file__))
RAW, OUT = os.path.join(HERE, f"raw_{DEV}"), os.path.join(HERE, f"out_{DEV}")
os.makedirs(OUT, exist_ok=True)
CC, CC_LABEL = CFG["cc"], CFG["cc_label"]
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
S, R = load(f"{DEV}_ID3_set.txt"), load(f"{DEV}_ID4_reset.txt")
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
    fh.write(f"# Device {DEV}, {M.cycle.nunique()} consecutive DC cycles, CC = {CC_LABEL} (SMU limit {CC*1e6:.0f} uA), "
             "TE biased, BE grounded\n")
    IV.to_csv(fh, sep="\t", index=False, float_format="%.6e")

# representative cycle: complete reads, closest to the median in log R and Vset (cycle 1 = first after forming)
full = M[M.cycle > 1].dropna(subset=["HRS_SET_ohm", "LRS_SET_ohm", "LRS_RESET_ohm", "HRS_RESET_ohm"])
z = np.log10(full[["HRS_SET_ohm", "LRS_SET_ohm", "LRS_RESET_ohm", "HRS_RESET_ohm"]]).join(full.Vset_V)
z = (z - z.median()) / (z.max() - z.min())
REP = int(full.loc[z.abs().sum(axis=1).idxmin(), "cycle"])


# ---- figure pieces -----------------------------------------------------------------------
def draw_forming(ax):
    F = load(f"{DEV}_ID2_forming.txt")
    ax.plot(F.V, F.I.abs(), color="#333", lw=2)
    kf = np.where(F.I.values >= 0.9 * CC)[0][0]
    if CFG["formed"]:
        ax.annotate(f"$V_{{form}}$ ≈ {F.V.values[kf]:.1f} V", xy=(F.V.values[kf], CC),
                    xytext=(F.V.values[kf] + 0.8, 3e-7), arrowprops=dict(arrowstyle="->", color="#333"), fontsize=12)
    else:
        up = F.iloc[:np.argmax(F.V.values) + 1]                       # upward sweep only
        k1 = np.argmin(np.abs(up.V.values - 0.1))
        ax.text(0.97, 0.12, f"no abrupt forming:\nalready {abs(up.V.values[k1] / up.I.values[k1]) / 1e3:.0f} kΩ at 0.1 V,\n"
                f"reaches CC at {F.V.values[kf]:.1f} V", transform=ax.transAxes, ha="right", va="bottom", fontsize=11)
    ax.axhline(CC, color="#555", ls="--", lw=1)
    ax.set_yscale("log"); ax.set_ylim(1e-12, 1e-3); log_minor(ax)
    ax.set_xlabel(r"$V_{TE}$ (V)"); ax.set_ylabel(r"$|I_{TE}|$ (A)")
    ax.text(0.97, 0.96, f"CC = {CC_LABEL}", transform=ax.transAxes, ha="right", va="top", fontsize=11, color="#333")


def draw_iv(ax):
    iv = IV if CFG["v_pos_max"] is None else IV[IV.V_TE_V <= CFG["v_pos_max"] + 1e-3]   # display only
    for (_, _), d in iv.groupby(["cycle", "sweep"]):
        ax.plot(d.V_TE_V, d.I_TE_A.abs(), color=GREY, lw=0.6, alpha=0.8, zorder=1)
    r = iv[iv.cycle == REP]
    for sweep, col in (("SET", BLUE), ("RESET", RED)):
        d = r[r.sweep == sweep]
        ax.plot(d.V_TE_V, d.I_TE_A.abs(), color=col, lw=2.2, zorder=3, label=f"{sweep} (cycle {REP})")
    ax.plot([], [], color=GREY, lw=1, label=f"{M.cycle.nunique()} cycles")
    ax.axhline(CC, color="#555", ls="--", lw=1, zorder=2)
    ax.axvline(0, color="#888", lw=0.8, zorder=0)
    ax.set_yscale("log"); ax.set_ylim(1e-10, 1e-2); log_minor(ax)
    vmax = CFG["v_pos_max"] or IV.V_TE_V.max()
    ax.set_xlim(IV.V_TE_V.min() - 0.2, vmax + 0.2)
    ax.set_xlabel(r"$V_{TE}$ (V)"); ax.set_ylabel(r"$|I_{TE}|$ (A)")
    ax.text(0.97, 0.96, f"CC = {CC_LABEL}", transform=ax.transAxes, ha="right", va="top", color="#333", fontsize=11)
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
    top = np.nanmax(np.r_[M.ON_OFF_SET, M.ON_OFF_RESET])
    ax_w.set_yscale("log"); ax_w.set_ylim(0.7, 10 ** (np.log10(top) + 1.3)); log_minor(ax_w)
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
ax.set_title(f"Forming (device {DEV})", fontsize=12, style="italic", color="#333"); fig.tight_layout(); save(fig, "forming")

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
print(f"SET-sweep LRS at compliance (R <= {V_READ / CC / 1e3:.2f} kOhm, not plotted): cycles",
      M.cycle[M.LRS_SET_ohm.isna()].tolist())
print("cycles with ON/OFF < 10 (SET / RESET):", int((M.ON_OFF_SET < 10).sum()), "/", int((M.ON_OFF_RESET < 10).sum()))
