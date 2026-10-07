"""Most-stable 50 cycles: the 50 valid cycles whose HRS and LRS (read at +/-0.1 V) lie in the narrowest band.

Selection (run analyze_best50.py first for the validity flags):
  1. Valid cycles only (see analyze_best50.py).
  2. Read log10 R at +0.1 V (HRS before SET, LRS after SET) and -0.1 V (LRS before RESET, HRS after RESET).
  3. Grid-search a band center c = (HRS+, LRS, HRS-) that minimises the half-width needed to hold 50 cycles
     (max deviation over the four reads, in decades); keep those 50 cycles.
  4. Plot them in measurement order (2_21 first, then TE_SET) as "selected cycle no." 1..50.
The cycles are NOT consecutive: the run and original cycle number of every point are in stable50_metrics.txt.

Outputs (out/): stable50_metrics.txt, stable50_IV_data.txt, stable50_endurance_0p1V.png,
                stable50_endurance_4reads.png, stable50_IV_semilog.png
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
N_SEL = 50
V_TOL = 0.01


def load(fname):
    d = pd.read_csv(os.path.join(RAW, fname), sep="\t", skiprows=[1, 2], na_values=["--"])
    d = d.rename(columns=lambda c: c.replace("_set", "").replace("_reset", ""))
    return d.rename(columns={"Loop2 Index": "loop", "SMU_TE Voltage": "V", "SMU_TE Current": "I"})[["loop", "V", "I"]]


def read_R(v, i, target):
    k = np.argmin(np.abs(np.abs(v) - target))
    if abs(abs(v[k]) - target) > V_TOL or i[k] == 0 or abs(i[k]) >= 0.95 * CC:
        return np.nan
    return abs(v[k] / i[k])


M = pd.read_csv(os.path.join(OUT, "cycle_metrics_all.txt"), sep="\t")
data = {run: (load(fs), load(fr)) for run, (fs, fr) in RUNS.items()}
rows, curves = [], {}
for _, b in M[M.valid].iterrows():
    S, R = data[b.run]
    s, r = S[S.loop == b.cycle], R[R.loop == b.cycle]
    curves[(b.run, b.cycle)] = (s, r)
    vs, is_, vr, ir = s.V.values, s.I.values, r.V.values, r.I.values
    ks, kr = np.argmax(vs), np.argmin(vr)
    row = {"run": b.run, "cycle": b.cycle, "Vset_V": b.Vset_V, "Vreset_V": b.Vreset_V}
    for vr_ in (0.05, 0.1):
        t = f"{vr_:g}V"
        row[f"HRS_pos_{t}"] = read_R(vs[:ks + 1], is_[:ks + 1], vr_)
        row[f"LRS_pos_{t}"] = read_R(vs[ks:], is_[ks:], vr_)
        row[f"LRS_neg_{t}"] = read_R(vr[:kr + 1], ir[:kr + 1], vr_)
        row[f"HRS_neg_{t}"] = read_R(vr[kr:], ir[kr:], vr_)
    rows.append(row)
A = pd.DataFrame(rows)

# ---- band search on the four 0.1 V reads ------------------------------------------------
KEYS = ["HRS_pos_0.1V", "LRS_pos_0.1V", "LRS_neg_0.1V", "HRS_neg_0.1V"]
L = np.log10(A[KEYS].values)
best = None
for hp in np.arange(6.0, 9.0, 0.05):
    for hn in np.arange(6.0, 9.0, 0.05):
        for lr in np.arange(3.0, 5.5, 0.05):
            dev = np.abs(L - [hp, lr, lr, hn]).max(axis=1)
            w = np.sort(dev)[N_SEL - 1]
            if best is None or w < best[0]:
                best = (w, np.array([hp, lr, lr, hn]))
half_width, center = best
dev = np.abs(L - center).max(axis=1)
S = A.iloc[np.sort(np.argsort(dev)[:N_SEL])].copy()
S = S.sort_values(["run", "cycle"], key=lambda c: c.map({"2_21": 0, "TE_SET": 1}) if c.name == "run" else c)
S.insert(0, "sel_no", range(1, len(S) + 1))
for vr_ in (0.05, 0.1):
    for pol in ("pos", "neg"):
        t = f"{pol}_{vr_:g}V"
        S[f"ONOFF_{t}"] = S[f"HRS_{t}"] / S[f"LRS_{t}"]
S.to_csv(os.path.join(OUT, "stable50_metrics.txt"), sep="\t", index=False, float_format="%.6g", na_rep="NaN")

parts = []
for _, b in S.iterrows():
    s, r = curves[(b.run, b.cycle)]
    for sweep, d in (("SET", s), ("RESET", r)):
        parts.append(pd.DataFrame({"sel_no": b.sel_no, "run": b.run, "cycle": b.cycle, "sweep": sweep,
                                   "V_TE_V": d.V.values, "I_TE_A": d.I.values}))
with open(os.path.join(OUT, "stable50_IV_data.txt"), "w") as fh:
    fh.write("# 1R RRAM, 50 most stable DC cycles (narrowest HRS/LRS band at +/-0.1 V), CC = 0.1 mA. "
             "Non-consecutive: see run/cycle columns\n")
    pd.concat(parts, ignore_index=True).to_csv(fh, sep="\t", index=False, float_format="%.6e")

# ---- plots -----------------------------------------------------------------------------
plt.rcParams.update({"font.size": 12, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": "#ececec", "grid.linewidth": 0.6})
C_HRS, C_LRS = "#c0392b", "#1f5fa8"
YLIM = (1e2, 1e10)
FOOT = (f"50 selected (non-consecutive) cycles: 1–{(S.run == '2_21').sum()} from run 2_21, "
        f"{(S.run == '2_21').sum() + 1}–{len(S)} from run TE_SET. CC = 0.1 mA.")


def panel(ax, vr_, pol):
    t = f"{pol}_{vr_:g}V"
    sign = "+" if pol == "pos" else "−"
    for st, col, mk in (("HRS", C_HRS, "o"), ("LRS", C_LRS, "s")):
        ax.semilogy(S.sel_no, S[f"{st}_{t}"], mk + "-", color=col, ms=6, lw=1.2, mec="white", mew=0.6, label=st)
    ax.set_ylim(*YLIM)
    ax.set_xlim(0, N_SEL + 1)
    n = S[f"HRS_{t}"].notna().sum()
    med = np.nanmedian(S[f"ONOFF_{t}"])
    ax.set_title(f"Read at {sign}{vr_:g} V" + (f"   (median ON/OFF ≈ {med:.1e})" if n else ""), fontsize=12)
    if n < len(S):
        ax.text(0.02, 0.5, "run 2_21 has no\n±0.05 V point", transform=ax.transAxes, color="#777", fontsize=9)
    ax.set_ylabel("Resistance (Ω)")


fig, axs = plt.subplots(1, 2, figsize=(12, 4.8), sharey=True)
for ax, pol in zip(axs, ("pos", "neg")):
    panel(ax, 0.1, pol)
    ax.set_xlabel("Selected cycle no.")
axs[0].legend(frameon=False, loc="center right")
fig.text(0.5, -0.01, FOOT, ha="center", fontsize=9, color="#666")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "stable50_endurance_0p1V.png"), dpi=300, bbox_inches="tight")
plt.close(fig)

fig, axs = plt.subplots(2, 2, figsize=(12, 8), sharex=True, sharey=True)
for i, vr_ in enumerate((0.05, 0.1)):
    for j, pol in enumerate(("pos", "neg")):
        panel(axs[i, j], vr_, pol)
for ax in axs[1]:
    ax.set_xlabel("Selected cycle no.")
axs[1, 0].legend(frameon=False, loc="center right")
fig.text(0.5, -0.01, FOOT, ha="center", fontsize=9, color="#666")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "stable50_endurance_4reads.png"), dpi=300, bbox_inches="tight")
plt.close(fig)

cmap = plt.get_cmap("Blues")
fig, ax = plt.subplots(figsize=(6.5, 5))
for k, (_, b) in enumerate(S.iterrows()):
    s, r = curves[(b.run, b.cycle)]
    for d in (s, r):
        ax.plot(d.V, np.abs(d.I), color=cmap(0.35 + 0.6 * k / (len(S) - 1)), lw=1, alpha=0.8)
ax.set_yscale("log"); ax.set_xlabel("Voltage (V)"); ax.set_ylabel("|Current| (A)")
ax.axhline(CC, color="#555", ls="--", lw=1); ax.text(3.0, CC * 1.4, "CC = 0.1 mA", color="#555", fontsize=9)
ax.set_title("1R RRAM: 50 most stable I-V cycles")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "stable50_IV_semilog.png"), dpi=300); plt.close(fig)

# ---- console summary: compare with the previous best-50 -----------------------------------
B = pd.read_csv(os.path.join(OUT, "endurance_read_voltages.txt"), sep="\t")
print(f"band center (log10 Ω) {center.round(2)}, half-width {half_width:.2f} decades; runs {S.run.value_counts().to_dict()}")
for k in KEYS:
    for name, D in (("best50", B), ("stable50", S)):
        lg = np.log10(D[k])
        print(f"{k:14s} {name:8s} median {np.median(D[k]):.3g}  spread {lg.max() - lg.min():.2f} dec  "
              f"mean |cycle-to-cycle jump| {np.abs(np.diff(lg)).mean():.2f} dec")
for t in ("pos_0.1V", "neg_0.1V"):
    print(t, "ON/OFF min", f"{S[f'ONOFF_{t}'].min():.3g}", "median", f"{S[f'ONOFF_{t}'].median():.3g}")
