"""1T1R (IGZO TFT + RRAM), 2 x 2 overlap area: forming removed, failed-SET cycles removed, publication-style plots
and endurance read at |V| = 0.05 V and 0.1 V.

Raw (raw_1T1R_2x2/), measured 2026-06-18:
  TE_SET_ID3-2.txt  50 SET loops,   V_TE 0 -> +4 V -> 0, 0.05 V steps, V_G = 6.69 V
  TE_SET_ID4-3.txt  50 RESET loops, V_TE 0 -> -4 V -> 0, 0.05 V steps, V_G = 7.0 V
  SET loop n is followed by RESET loop n (one cycle).
Not used: TE_SET_ID1-1*.txt (timestamp only); TE_SET_ID3-2_20260914_180932.txt (a separate 2026-09-14 session:
4 SET loops at V_G = 5.8 V, the last one cut off, and no RESET file).

Cycle selection (rules, not hand-picking):
  forming : SET loop 1 starts pristine (~0.4 nA at 0.1 V) and forms abruptly at ~3.05 V into the 1 mA SMU limit
            -> cycle 1 is the forming cycle and is removed.
  bad     : failed / incomplete SET = SET-sweep LRS > 2 x the median LRS of the remaining cycles -> removed.
Read rules at |V| = V_read: SET sweep HRS = up branch, LRS = down branch; RESET sweep LRS = out branch, HRS = back
branch. R includes the TFT channel in series (1T1R).

Outputs (out_1T1R_2x2/): cycle_metrics.txt (all 50 cycles, kept flag + reason), IV_kept_cycles.txt, summary.txt,
IV / endurance_0p1V / endurance_0p05V / endurance_compare / combined  (.png + .pdf)
Run:  python plot_1T1R_2x2.py
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import LogLocator, NullFormatter

HERE = os.path.dirname(os.path.abspath(__file__))
RAW, OUT = os.path.join(HERE, "raw_1T1R_2x2"), os.path.join(HERE, "out_1T1R_2x2")
os.makedirs(OUT, exist_ok=True)
V_READS = (0.05, 0.1)
V_TOL = 0.01
BAD_LRS_FACTOR = 2.0
DEVICE_LABEL = "1T1R, IGZO 2 × 2 overlap"
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
    d.columns = [c.replace("_set", "").replace("_reset", "").replace("SMU_G2", "SMU_G") for c in d.columns]
    return d.rename(columns={"Loop Index": "loop", "SMU_TE Voltage": "V", "SMU_TE Current": "I", "SMU_G Voltage": "VG"})


def read_R(branch, v_read):
    k = np.argmin(np.abs(branch.V.abs().values - v_read))
    v, i = branch.V.values[k], branch.I.values[k]
    return abs(v / i) if abs(abs(v) - v_read) <= V_TOL and i != 0 else np.nan


def log_minor(ax):
    ax.yaxis.set_minor_locator(LogLocator(base=10, subs=np.arange(2, 10) * 0.1, numticks=50))
    ax.yaxis.set_minor_formatter(NullFormatter())


# ---- per-cycle metrics -------------------------------------------------------------------
S, R = load("TE_SET_ID3-2.txt"), load("TE_SET_ID4-3.txt")
VG_SET, VG_RESET = S.VG.median(), R.VG.median()
rows, curves = [], {}
for n in sorted(set(S.loop) & set(R.loop)):
    s, r = S[S.loop == n], R[R.loop == n]
    curves[n] = (s, r)
    ks, kr = np.argmax(s.V.values), np.argmin(r.V.values)
    up, down, out, back = s.iloc[:ks + 1], s.iloc[ks:], r.iloc[:kr + 1], r.iloc[kr:]
    row = {"cycle": n, "Vmax_SET_V": s.V.max(), "Imax_SET_A": s.I.max(), "Imax_RESET_A": -r.I.min()}
    # SET voltage: largest current step on the up branch (abrupt or gradual, it marks the switching point)
    # (search from 0.2 V: below that the first step out of the noise floor dominates)
    dI = np.diff(np.log10(np.clip(up.I.values, 1e-12, None)))
    dI[up.V.values[1:] < 0.2] = -np.inf
    row["Vset_V"] = up.V.values[np.argmax(dI) + 1]
    for vr in V_READS:
        t = f"{vr:g}V"
        row[f"HRS_SET_{t}"], row[f"LRS_SET_{t}"] = read_R(up, vr), read_R(down, vr)
        row[f"LRS_RESET_{t}"], row[f"HRS_RESET_{t}"] = read_R(out, vr), read_R(back, vr)
        row[f"ONOFF_SET_{t}"] = row[f"HRS_SET_{t}"] / row[f"LRS_SET_{t}"]
        row[f"ONOFF_RESET_{t}"] = row[f"HRS_RESET_{t}"] / row[f"LRS_RESET_{t}"]
    rows.append(row)
M = pd.DataFrame(rows)

# ---- selection rules ---------------------------------------------------------------------
M["kept"], M["reason"] = True, ""
first = curves[1][0]
pristine = read_R(first.iloc[:np.argmax(first.V.values) + 1], 0.1)
M.loc[M.cycle == 1, ["kept", "reason"]] = [False, f"forming (pristine {pristine / 1e6:.0f} MOhm at 0.1 V)"]
lrs_med = M.loc[M.kept, "LRS_SET_0.1V"].median()
bad = M.kept & (M["LRS_SET_0.1V"] > BAD_LRS_FACTOR * lrs_med)
M.loc[bad, "kept"] = False
M.loc[bad, "reason"] = [f"failed SET (LRS {x / 1e3:.1f} kOhm > {BAD_LRS_FACTOR:g} x median {lrs_med / 1e3:.1f} kOhm)"
                        for x in M.loc[bad, "LRS_SET_0.1V"]]
K = M[M.kept].reset_index(drop=True)
N = len(K)
M.to_csv(os.path.join(OUT, "cycle_metrics.txt"), sep="\t", index=False, float_format="%.6g", na_rep="NaN")

parts = []
for n in K.cycle:
    s, r = curves[n]
    for sweep, d in (("SET", s), ("RESET", r)):
        parts.append(pd.DataFrame({"cycle": n, "sweep": sweep, "V_TE_V": d.V.values, "I_TE_A": d.I.values}))
IV = pd.concat(parts, ignore_index=True)
with open(os.path.join(OUT, "IV_kept_cycles.txt"), "w") as fh:
    fh.write(f"# {DEVICE_LABEL}, {N} cycles (forming + failed SETs removed), V_G(SET) = {VG_SET:.2f} V, "
             f"V_G(RESET) = {VG_RESET:.2f} V\n")
    IV.to_csv(fh, sep="\t", index=False, float_format="%.6e")

# highlighted cycle = the "best" cycle: widest SET and RESET hysteresis loops and the largest window. Score = sum of
# the ranks of (SET loop area, RESET loop area, min(ON/OFF SET, ON/OFF RESET) at 0.1 V); loop area = integral over
# |V| = 0.1-2 V of the log10-current gap between the two branches of a sweep (decades x V).
def loop_area(a, b):
    g = np.arange(0.1, 2.0001, 0.05)
    la = np.interp(g, a.V.abs(), np.log10(a.I.abs() + 1e-13))
    lb = np.interp(g, b.V.abs(), np.log10(b.I.abs() + 1e-13))
    return np.trapezoid(la - lb, g)


areas = []
for n in K.cycle:
    s_, r_ = curves[n]
    ks, kr = np.argmax(s_.V.values), np.argmin(r_.V.values)
    areas.append((loop_area(s_.iloc[ks:].iloc[::-1], s_.iloc[:ks + 1]),
                  loop_area(r_.iloc[:kr + 1], r_.iloc[kr:].iloc[::-1])))
K["SET_loop_area"], K["RESET_loop_area"] = zip(*areas)
score = (K.SET_loop_area.rank() + K.RESET_loop_area.rank()
         + np.minimum(K["ONOFF_SET_0.1V"], K["ONOFF_RESET_0.1V"]).rank())
REP = int(K.loc[score.idxmax(), "cycle"])

# ---- summary (median is the number to report; mean shown for comparison) --------------------
summ = []
for vr in V_READS:
    t = f"{vr:g}V"
    for q in ("ONOFF_SET", "ONOFF_RESET", "HRS_SET", "LRS_SET", "LRS_RESET", "HRS_RESET"):
        x = K[f"{q}_{t}"]
        summ.append({"read": f"{vr * 1e3:.0f} mV", "quantity": q, "median": x.median(), "mean": x.mean(),
                     "geo_mean": 10 ** np.log10(x).mean(), "min": x.min(), "max": x.max(),
                     "P10": x.quantile(0.1), "P90": x.quantile(0.9)})
summ = pd.DataFrame(summ)
with open(os.path.join(OUT, "summary.txt"), "w") as fh:
    fh.write(f"# {DEVICE_LABEL}: {N} cycles kept of {len(M)}; removed: "
             + "; ".join(f"cycle {c}: {r}" for c, r in zip(M.cycle[~M.kept], M.reason[~M.kept])) + "\n")
    fh.write(f"# V_G(SET) = {VG_SET:.2f} V, V_G(RESET) = {VG_RESET:.2f} V, highlighted (best) cycle {REP}\n")
    summ.to_csv(fh, sep="\t", index=False, float_format="%.4g")


# ---- figure pieces -----------------------------------------------------------------------
def draw_iv(ax):
    for (_, _), d in IV.groupby(["cycle", "sweep"]):
        ax.plot(d.V_TE_V, d.I_TE_A.abs(), color=GREY, lw=0.6, alpha=0.8, zorder=1)
    r = IV[IV.cycle == REP]
    for sweep, col in (("SET", BLUE), ("RESET", RED)):
        d = r[r.sweep == sweep]
        ax.plot(d.V_TE_V, d.I_TE_A.abs(), color=col, lw=2.2, zorder=3, label=sweep)
    ax.plot([], [], color=GREY, lw=1, label=f"{N} cycles")
    ax.axvline(0, color="#888", lw=0.8, zorder=0)
    ax.set_yscale("log"); ax.set_ylim(1e-10, 1e-2); log_minor(ax)
    ax.set_xlim(-4.3, 4.3)
    ax.set_xlabel(r"$V_{TE}$ (V)"); ax.set_ylabel(r"$|I_{TE}|$ (A)")
    ax.text(0.97, 0.96, rf"$V_{{GS}}$(SET) = +{VG_SET:.1f} V", transform=ax.transAxes, ha="right", va="top",
            color=BLUE, fontsize=11)
    ax.text(0.97, 0.90, rf"$V_{{GS}}$(RESET) = +{VG_RESET:.1f} V", transform=ax.transAxes, ha="right", va="top",
            color=RED, fontsize=11)
    ax.text(0.03, 0.96, DEVICE_LABEL, transform=ax.transAxes, ha="left", va="top", color="#444", fontsize=10)
    # mark the SET jump of the highlighted cycle (largest single-step current rise above 0.2 V)
    up = r[r.sweep == "SET"]
    up = up.iloc[:np.argmax(up.V_TE_V.values) + 1]
    up = up[up.V_TE_V >= 0.2]
    kj = np.argmax(np.diff(np.log10(up.I_TE_A.abs().values))) + 1
    vj, ij = up.V_TE_V.values[kj], up.I_TE_A.abs().values[kj]
    ax.annotate(f"SET ≈ {vj:.1f} V", xy=(vj, ij), xytext=(vj + 0.9, ij / 30), color=BLUE, fontsize=11,
                arrowprops=dict(arrowstyle="->", color=BLUE, lw=1.2))
    ax.legend(loc="lower left", title=f"best cycle ({REP})", title_fontsize=10)


def draw_endurance(ax_r, ax_w, vr, legend=True):
    t = f"{vr:g}V"
    x = K.cycle
    kw = dict(s=26, linewidths=1.0, zorder=3)
    ax_r.scatter(x, K[f"HRS_SET_{t}"], marker="o", facecolors="none", edgecolors=BLUE, label="HRS (SET sweep)", **kw)
    ax_r.scatter(x, K[f"LRS_SET_{t}"], marker="o", color=BLUE, label="LRS (SET sweep)", s=14, zorder=4)
    ax_r.scatter(x, K[f"HRS_RESET_{t}"], marker="s", facecolors="none", edgecolors=RED, label="HRS (RESET sweep)", **kw)
    ax_r.scatter(x, K[f"LRS_RESET_{t}"], marker="s", color=RED, label="LRS (RESET sweep)", s=34, zorder=3)
    ax_r.set_yscale("log"); ax_r.set_ylim(2e3, 3e5); log_minor(ax_r)
    ax_r.set_ylabel(r"$R$ at $V_{read}$ ($\Omega$)")
    if legend:
        h, l = ax_r.get_legend_handles_labels()
        ax_r.legend([h[i] for i in (0, 2, 1, 3)], [l[i] for i in (0, 2, 1, 3)], ncol=2, fontsize=9.5,
                    loc="lower center", bbox_to_anchor=(0.5, 1.01), handletextpad=0.3, columnspacing=1.0,
                    title=rf"read at $|V|$ = {vr * 1e3:.0f} mV", title_fontsize=10)
    else:
        ax_r.set_title(rf"read at $|V|$ = {vr * 1e3:.0f} mV", fontsize=12)
    ax_r.tick_params(labelbottom=False)
    ax_w.scatter(x, K[f"ONOFF_SET_{t}"], marker="o", color=BLUE, s=18, label="SET", zorder=3)
    ax_w.scatter(x, K[f"ONOFF_RESET_{t}"], marker="s", color=RED, s=18, label="RESET", zorder=3)
    ax_w.axhline(10, color="#999", ls="--", lw=1)
    ax_w.set_yscale("log"); ax_w.set_ylim(1, 100); log_minor(ax_w)
    ax_w.set_ylabel(r"$R_{HRS}/R_{LRS}$"); ax_w.set_xlabel("Cycle")
    ax_w.legend(ncol=2, loc="upper center", frameon=False, fontsize=10, handletextpad=0.2)
    ax_w.set_xlim(0, M.cycle.max() + 2)


def endurance_axes(fig, spec):
    sub = spec.subgridspec(2, 1, height_ratios=[2.3, 1], hspace=0.08)
    ax_r = fig.add_subplot(sub[0])
    return ax_r, fig.add_subplot(sub[1], sharex=ax_r)


def save(fig, name, **kw):
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(OUT, f"{name}.{ext}"), dpi=300, **kw)
    plt.close(fig)


def med(q, vr):
    return K[f"{q}_{vr:g}V"].median()


EXCL = "Excluded: " + ", ".join(f"cycle {c} ({'forming' if c == 1 else 'failed SET'})" for c in M.cycle[~M.kept])

fig, ax = plt.subplots(figsize=(6.2, 5.2)); draw_iv(ax)
ax.set_title("Bipolar I-V (SET/RESET)", fontsize=12, style="italic", color="#333"); fig.tight_layout(); save(fig, "IV")

for vr in V_READS:
    fig = plt.figure(figsize=(6.6, 6.0)); draw_endurance(*endurance_axes(fig, fig.add_gridspec(1, 1)[0]), vr)
    fig.text(0.5, 0.005, EXCL, ha="center", fontsize=8.5, color="#666")
    fig.tight_layout(rect=(0, 0.02, 1, 1)); save(fig, f"endurance_0p{vr * 100:02.0f}V".replace("0p05", "0p05").replace("0p10", "0p1"))

fig = plt.figure(figsize=(13.2, 6.2))
gs = fig.add_gridspec(1, 2, wspace=0.25)
for j, vr in enumerate(V_READS):
    ax_r, ax_w = endurance_axes(fig, gs[j])
    draw_endurance(ax_r, ax_w, vr, legend=False)
    fig.text(0.29 + 0.44 * j, -0.01, f"{vr * 1e3:.0f} mV read — median window SET {med('ONOFF_SET', vr):.1f}×, "
             f"RESET {med('ONOFF_RESET', vr):.1f}×", ha="center", style="italic", color="#3a4a6b", fontsize=11)
h, l = ax_r.get_legend_handles_labels()
fig.legend([h[i] for i in (0, 2, 1, 3)], [l[i] for i in (0, 2, 1, 3)], ncol=4, fontsize=10.5,
           loc="lower center", bbox_to_anchor=(0.5, 0.93), handletextpad=0.3, columnspacing=1.5)
fig.text(0.5, -0.05, EXCL, ha="center", fontsize=9, color="#666")
save(fig, "endurance_compare", bbox_inches="tight")

fig = plt.figure(figsize=(13.2, 5.6))
gs = fig.add_gridspec(1, 2, width_ratios=[1, 1.05], wspace=0.28)
draw_iv(fig.add_subplot(gs[0]))
draw_endurance(*endurance_axes(fig, gs[1]), 0.1)
fig.text(0.29, -0.01, "Bipolar I-V (SET/RESET)", ha="center", style="italic", color="#3a4a6b", fontsize=12)
fig.text(0.73, -0.01, f"Endurance / Window (SET: {med('ONOFF_SET', 0.1):.1f}×, RESET: {med('ONOFF_RESET', 0.1):.1f}×)",
         ha="center", style="italic", color="#3a4a6b", fontsize=12)
fig.text(0.5, -0.05, EXCL, ha="center", fontsize=9, color="#666")
save(fig, "combined", bbox_inches="tight")

print(f"kept {N} of {len(M)}; removed:", dict(zip(M.cycle[~M.kept], M.reason[~M.kept])))
print(f"V_G SET {VG_SET:.3f} V, RESET {VG_RESET:.3f} V; highlighted (best) cycle {REP}; LRS median used for rule {lrs_med:.0f}")
print(summ.to_string(index=False, float_format="%.4g"))
print("Vset median", K.Vset_V.median(), " cycles with window < 10x @0.1V (SET/RESET):",
      int((K["ONOFF_SET_0.1V"] < 10).sum()), int((K["ONOFF_RESET_0.1V"] < 10).sum()))
