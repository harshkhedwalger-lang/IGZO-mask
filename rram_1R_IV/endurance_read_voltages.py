"""Endurance of the best-50 cycles read at +/-0.05 V and +/-0.1 V (run analyze_best50.py first).

Where each state is read inside one cycle (SET n -> RESET n):
  +V  HRS : SET forward branch, before switching (state left by RESET n-1)
  +V  LRS : SET return branch, after switching (rejected if still at compliance)
  -V  LRS : RESET forward branch, before switching
  -V  HRS : RESET return branch, after switching
Run 2_21 used 0.1 V steps, so it has no +/-0.05 V point -> those reads are left empty (no interpolation).

Outputs (out/): endurance_read_voltages.txt, endurance_read_voltages.png, endurance_read_voltages_by_run.png
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
RAW, OUT = os.path.join(HERE, "raw"), os.path.join(HERE, "out")
RUNS = {"2_21": ("2_21_ID3_set.txt", "2_21_ID4_reset.txt"),
        "TE_SET": ("TE_SET_ID3_set.txt", "TE_SET_ID4_reset.txt")}
CC = 110e-6
V_READS = (0.05, 0.1)
V_TOL = 0.01         # a measured point must lie within 10 mV of the read voltage


def load(fname):
    d = pd.read_csv(os.path.join(RAW, fname), sep="\t", skiprows=[1, 2], na_values=["--"])
    d = d.rename(columns=lambda c: c.replace("_set", "").replace("_reset", ""))
    return d.rename(columns={"Loop2 Index": "loop", "SMU_TE Voltage": "V", "SMU_TE Current": "I"})[["loop", "V", "I"]]


def read_R(v, i, target):
    """|V/I| at the measured point closest to |V| = target; NaN if no point within V_TOL or at compliance."""
    k = np.argmin(np.abs(np.abs(v) - target))
    if abs(abs(v[k]) - target) > V_TOL or i[k] == 0 or abs(i[k]) >= 0.95 * CC:
        return np.nan
    return abs(v[k] / i[k])


best = pd.read_csv(os.path.join(OUT, "best50_metrics.txt"), sep="\t")
data = {run: (load(fs), load(fr)) for run, (fs, fr) in RUNS.items()}

rows = []
for _, b in best.iterrows():
    S, R = data[b.run]
    s, r = S[S.loop == b.cycle], R[R.loop == b.cycle]
    vs, is_, vr, ir = s.V.values, s.I.values, r.V.values, r.I.values
    ks, kr = np.argmax(vs), np.argmin(vr)
    row = {"best_no": b.best_no, "run": b.run, "cycle": b.cycle}
    for vr_ in V_READS:
        t = f"{vr_:g}V"
        row[f"HRS_pos_{t}"] = read_R(vs[:ks + 1], is_[:ks + 1], vr_)
        row[f"LRS_pos_{t}"] = read_R(vs[ks:], is_[ks:], vr_)
        row[f"LRS_neg_{t}"] = read_R(vr[:kr + 1], ir[:kr + 1], vr_)
        row[f"HRS_neg_{t}"] = read_R(vr[kr:], ir[kr:], vr_)
    rows.append(row)
E = pd.DataFrame(rows)
for vr_ in V_READS:
    for pol in ("pos", "neg"):
        t = f"{pol}_{vr_:g}V"
        E[f"ONOFF_{t}"] = E[f"HRS_{t}"] / E[f"LRS_{t}"]
E.to_csv(os.path.join(OUT, "endurance_read_voltages.txt"), sep="\t", index=False, float_format="%.6g", na_rep="NaN")

# ---- plot: 2 x 2 grid, rows = read voltage, columns = polarity --------------------------
plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": "#e5e5e5", "grid.linewidth": 0.6})
C_HRS, C_LRS = "#c0392b", "#1f5fa8"
run_edge = E.run.ne(E.run.shift()).cumsum()            # boundary between the two runs
x_split = E.best_no[run_edge.diff() == 1].min() - 0.5


def panel(ax, df, vr_, pol, x):
    t = f"{pol}_{vr_:g}V"
    sign = "+" if pol == "pos" else "−"
    gap = np.r_[False, np.diff(np.asarray(x)) > 1]      # break the line where cycles were skipped
    for st, col, mk in (("HRS", C_HRS, "o"), ("LRS", C_LRS, "s")):
        y = df[f"{st}_{t}"].values
        xs = np.insert(np.asarray(x, float), np.where(gap)[0], np.nan)
        ys = np.insert(y.astype(float), np.where(gap)[0], np.nan)
        ax.semilogy(xs, ys, mk + "-", color=col, ms=5, lw=1.5, label=st)
    ax.set_ylim(5e2, 3e10)
    med = np.nanmedian(df[f"ONOFF_{t}"])
    n = df[f"HRS_{t}"].notna().sum()
    ax.set_title(f"Read at {sign}{vr_:g} V  (n = {n}, median ON/OFF ≈ {med:.0f})" if n else
                 f"Read at {sign}{vr_:g} V  (no data)", fontsize=11)
    ax.set_ylabel("Resistance (Ω)")


fig, axs = plt.subplots(2, 2, figsize=(12, 8), sharex=True, sharey=True)
for i, vr_ in enumerate(V_READS):
    for j, pol in enumerate(("pos", "neg")):
        ax = axs[i, j]
        panel(ax, E, vr_, pol, E.best_no)
        ax.axvline(x_split, color="#888", ls=":", lw=1)
        ax.text(x_split / 2, 0.93, "2_21", transform=ax.get_xaxis_transform(), ha="center", va="bottom",
                color="#666", fontsize=9)
        ax.text((x_split + E.best_no.max()) / 2, 0.93, "TE_SET", transform=ax.get_xaxis_transform(),
                ha="center", va="bottom", color="#666", fontsize=9)
for ax in axs[1]:
    ax.set_xlabel("Best-cycle no.")
axs[0, 0].legend(frameon=False, loc="center left")
fig.suptitle("Endurance of best 50 cycles (CC = 0.1 mA) at different read voltages", y=1.0)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "endurance_read_voltages.png"), dpi=300); plt.close(fig)

# ---- plot: TE_SET only (the run that has all four read points), own cycle no. --------------
T = E[E.run == "TE_SET"]
fig, axs = plt.subplots(2, 2, figsize=(12, 8), sharex=True, sharey=True)
for i, vr_ in enumerate(V_READS):
    for j, pol in enumerate(("pos", "neg")):
        panel(axs[i, j], T, vr_, pol, T.cycle)
for ax in axs[1]:
    ax.set_xlabel("Cycle no. (TE_SET run)")
axs[0, 0].legend(frameon=False, loc="center left")
fig.suptitle("TE_SET run: 30 best cycles at ±0.05 V and ±0.1 V read", y=1.0)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "endurance_read_voltages_TE_SET.png"), dpi=300); plt.close(fig)

# console summary
summ = []
for vr_ in V_READS:
    for pol in ("pos", "neg"):
        t = f"{pol}_{vr_:g}V"
        summ.append({"read": f"{'+' if pol == 'pos' else '-'}{vr_:g} V", "n": E[f"HRS_{t}"].notna().sum(),
                     "LRS_med_kohm": np.nanmedian(E[f"LRS_{t}"]) / 1e3, "HRS_med_Mohm": np.nanmedian(E[f"HRS_{t}"]) / 1e6,
                     "ONOFF_med": np.nanmedian(E[f"ONOFF_{t}"]), "ONOFF_min": np.nanmin(E[f"ONOFF_{t}"])})
print(pd.DataFrame(summ).to_string(index=False, float_format="%.3g"))
print("NaN counts:\n", E.drop(columns=["best_no", "run", "cycle"]).isna().groupby(E.run).sum().T.to_string())
