"""1R HfO2 RRAM DC cycling, CC = 0.1 mA (SMU limit ~110 uA): pick the best 50 SET/RESET cycles.

Inputs  (raw/): <run>_ID3_set.txt + <run>_ID4_reset.txt for runs 2_21 (2026-08-11) and TE_SET (2026-08-24).
        Measurements are interleaved: SET loop n is followed by RESET loop n -> one cycle.
Outputs (out/): cycle_metrics_all.txt, best50_metrics.txt, best50_IV_data.txt, *.png

Run:  python analyze_best50.py
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
RAW, OUT = os.path.join(HERE, "raw"), os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)

RUNS = {"2_21": ("2_21_ID3_set.txt", "2_21_ID4_reset.txt"),
        "TE_SET": ("TE_SET_ID3_set.txt", "TE_SET_ID4_reset.txt")}
CC = 110e-6          # measured compliance plateau (nominal 0.1 mA)
V_READ = 0.2         # |V| at which LRS/HRS are read
N_BEST = 50
RATIO_MIN = 5        # minimum HRS/LRS for a RESET to count as successful
I_BREAKDOWN = 2e-3   # RESET current above this = hard-breakdown / leaky cycle, rejected


def load(fname):
    d = pd.read_csv(os.path.join(RAW, fname), sep="\t", skiprows=[1, 2], na_values=["--"])
    d = d.rename(columns=lambda c: c.replace("_set", "").replace("_reset", ""))
    return d.rename(columns={"Loop2 Index": "loop", "SMU_TE Voltage": "V", "SMU_TE Current": "I"})[["loop", "V", "I"]]


def read_R(v, i, target):
    """Resistance |V/I| at the point closest to |V| = target."""
    k = np.argmin(np.abs(np.abs(v) - target))
    return abs(v[k] / i[k]) if i[k] != 0 else np.nan


def cycle_metrics(s, r):
    vs, is_ = s.V.values, s.I.values
    vr, ir = r.V.values, r.I.values
    m = {}
    # SET: first point that reaches compliance on the forward sweep
    kpk = np.argmax(vs)
    hit = np.where(is_[:kpk + 1] >= 0.9 * CC)[0]
    m["set_ok"] = len(hit) > 0
    m["Vset_V"] = vs[hit[0]] if len(hit) else np.nan
    m["R_preSET_ohm"] = read_R(vs[:kpk + 1], is_[:kpk + 1], V_READ)  # state before SET must be HRS
    # RESET: peak |I| on forward (negative-going) sweep
    kmin = np.argmin(vr)
    fwd_v, fwd_i = vr[:kmin + 1], ir[:kmin + 1]
    kr = np.argmax(np.abs(fwd_i))
    m["Vreset_V"], m["Ireset_A"] = fwd_v[kr], abs(fwd_i[kr])
    m["Vstop_V"] = vr.min()
    m["n_reset_pts"] = len(vr)
    # LRS read on RESET forward branch, HRS read on RESET return branch
    m["R_LRS_ohm"] = read_R(fwd_v, fwd_i, V_READ)
    m["R_HRS_ohm"] = read_R(vr[kmin:], ir[kmin:], V_READ)
    m["ON_OFF"] = m["R_HRS_ohm"] / m["R_LRS_ohm"]
    return m


rows, curves = [], {}
for run, (fs, fr) in RUNS.items():
    S, R = load(fs), load(fr)
    for n in sorted(set(S.loop) & set(R.loop)):
        s, r = S[S.loop == n], R[R.loop == n]
        m = cycle_metrics(s, r)
        m.update(run=run, cycle=n)
        rows.append(m)
        curves[(run, n)] = (s, r)

M = pd.DataFrame(rows)
# Validity: complete sweep, SET reached CC, RESET opened the window, no breakdown-level current
complete = M.groupby("run").n_reset_pts.transform("median") <= M.n_reset_pts
M["valid"] = (M.set_ok & complete & (M.ON_OFF >= RATIO_MIN) & (M.Ireset_A < I_BREAKDOWN)
              & (M.R_preSET_ohm >= RATIO_MIN * M.R_LRS_ohm))

# Score valid cycles: large memory window + uniformity (close to population median)
v = M[M.valid]
def z(x):  # robust z-score
    mad = np.median(np.abs(x - np.median(x))) * 1.4826
    return np.abs(x - np.median(x)) / (mad if mad > 0 else 1)
M["score"] = np.nan
M.loc[v.index, "score"] = (np.log10(v.ON_OFF)
                           - 0.25 * (z(np.log10(v.R_LRS_ohm)) + z(np.log10(v.R_HRS_ohm))
                                     + z(v.Vset_V) + z(v.Vreset_V)))
M = M.sort_values(["run", "cycle"]).reset_index(drop=True)
best = M[M.valid].nlargest(N_BEST, "score").sort_values(["run", "cycle"]).reset_index(drop=True)
best.insert(0, "best_no", range(1, len(best) + 1))

cols = ["run", "cycle", "valid", "score", "Vset_V", "Vreset_V", "Ireset_A", "R_LRS_ohm", "R_HRS_ohm", "ON_OFF", "R_preSET_ohm", "Vstop_V"]
fmt = lambda df, f: df.to_csv(os.path.join(OUT, f), sep="\t", index=False, float_format="%.6g")
fmt(M[cols], "cycle_metrics_all.txt")
fmt(best[["best_no"] + cols], "best50_metrics.txt")

# Full I-V data of the 50 best cycles, one long table (Origin-friendly)
parts = []
for _, b in best.iterrows():
    s, r = curves[(b.run, b.cycle)]
    for sweep, d in (("SET", s), ("RESET", r)):
        parts.append(pd.DataFrame({"best_no": b.best_no, "run": b.run, "cycle": b.cycle,
                                   "sweep": sweep, "V_TE_V": d.V.values, "I_TE_A": d.I.values}))
iv = pd.concat(parts, ignore_index=True)
with open(os.path.join(OUT, "best50_IV_data.txt"), "w") as fh:
    fh.write(f"# 1R RRAM best {len(best)} DC cycles, CC = 0.1 mA (SMU limit {CC*1e6:.0f} uA), TE biased, BE grounded\n")
    iv.to_csv(fh, sep="\t", index=False, float_format="%.6e")

# Same data, wide layout: one V/I column pair per cycle (SET then RESET), paste straight into Origin
wide = pd.concat([pd.DataFrame({f"B{b}_{run}_c{c}_V": g.V_TE_V.values, f"B{b}_{run}_c{c}_I": g.I_TE_A.values})
                  for (b, run, c), g in iv.groupby(["best_no", "run", "cycle"], sort=True)], axis=1)
wide.to_csv(os.path.join(OUT, "best50_IV_wide.txt"), sep="\t", index=False, float_format="%.6e")

# ---- plots -----------------------------------------------------------------------------
plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": "#e5e5e5", "grid.linewidth": 0.6})
cmap = plt.get_cmap("Blues")
cols_c = [cmap(0.35 + 0.6 * k / max(len(best) - 1, 1)) for k in range(len(best))]

fig, ax = plt.subplots(figsize=(6.5, 5))
for k, (_, b) in enumerate(best.iterrows()):
    s, r = curves[(b.run, b.cycle)]
    for d in (s, r):
        ax.plot(d.V, np.abs(d.I), color=cols_c[k], lw=1, alpha=0.8)
ax.set_yscale("log")
ax.set_xlabel("Voltage (V)")
ax.set_ylabel("|Current| (A)")
ax.axhline(CC, color="#555", ls="--", lw=1)
ax.text(3.0, CC * 1.4, "CC = 0.1 mA", color="#555", fontsize=9)
ax.set_title(f"1R RRAM: best {len(best)} I-V cycles (CC = 0.1 mA)")
sm = plt.cm.ScalarMappable(cmap=matplotlib.colors.ListedColormap(cols_c),
                           norm=plt.Normalize(1, len(best)))
fig.colorbar(sm, ax=ax, label="Best-cycle no.")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "best50_IV_semilog.png"), dpi=300); plt.close(fig)

# per-run overlay, best cycles highlighted vs rejected in grey
fig, axs = plt.subplots(1, 2, figsize=(12, 4.8), sharey=True)
for ax, run in zip(axs, RUNS):
    sel = set(best[best.run == run].cycle)
    for (rn, n), (s, r) in curves.items():
        if rn != run:
            continue
        c, lw, z_ = ("#1f5fa8", 0.9, 2) if n in sel else ("#bbbbbb", 0.7, 1)
        for d in (s, r):
            ax.plot(d.V, np.abs(d.I), color=c, lw=lw, zorder=z_, alpha=0.8)
    ax.set_yscale("log"); ax.set_xlabel("Voltage (V)")
    ax.set_title(f"{run}: {len(sel)} selected (blue) / {sum(M.run == run)} cycles")
axs[0].set_ylabel("|Current| (A)")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "per_run_selected_vs_rejected.png"), dpi=200); plt.close(fig)

# endurance + CDFs of the 50 best
fig, axs = plt.subplots(1, 3, figsize=(15, 4.5))
x = best.best_no
axs[0].semilogy(x, best.R_HRS_ohm, "o-", color="#c0392b", ms=5, lw=1.5, label="HRS")
axs[0].semilogy(x, best.R_LRS_ohm, "s-", color="#1f5fa8", ms=5, lw=1.5, label="LRS")
axs[0].set_xlabel("Best-cycle no."); axs[0].set_ylabel(f"Resistance @ {V_READ} V (Ω)")
axs[0].set_title("Endurance (best 50)"); axs[0].legend(frameon=False)
for lab, col, mk in (("R_LRS_ohm", "#1f5fa8", "s"), ("R_HRS_ohm", "#c0392b", "o")):
    vals = np.sort(best[lab]); axs[1].semilogx(vals, np.linspace(0, 100, len(vals)), mk + "-",
                                               color=col, ms=4, lw=1.5, label=lab.split("_")[1])
axs[1].set_xlabel("Resistance (Ω)"); axs[1].set_ylabel("Cumulative probability (%)")
axs[1].set_title("Resistance distribution"); axs[1].legend(frameon=False)
for lab, col, mk in (("Vset_V", "#c0392b", "o"), ("Vreset_V", "#1f5fa8", "s")):
    vals = np.sort(best[lab]); axs[2].plot(vals, np.linspace(0, 100, len(vals)), mk + "-",
                                           color=col, ms=4, lw=1.5, label=lab.replace("_V", ""))
axs[2].set_xlabel("Voltage (V)"); axs[2].set_ylabel("Cumulative probability (%)")
axs[2].set_title("Switching-voltage distribution"); axs[2].legend(frameon=False)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "best50_endurance_cdf.png"), dpi=300); plt.close(fig)

# console summary
print(M.groupby("run").agg(cycles=("cycle", "size"), valid=("valid", "sum")))
print("selected per run:", best.run.value_counts().to_dict())
print(best[["Vset_V", "Vreset_V", "Ireset_A", "R_LRS_ohm", "R_HRS_ohm", "ON_OFF"]]
      .describe().loc[["mean", "std", "min", "50%", "max"]].to_string(float_format="%.4g"))
print("rejected:", M[~M.valid][["run", "cycle", "set_ok", "Vset_V", "R_preSET_ohm", "R_LRS_ohm", "ON_OFF", "Ireset_A", "n_reset_pts"]].to_string() if "set_ok" in M else "")
