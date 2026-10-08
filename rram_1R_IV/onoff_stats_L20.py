"""1T1R device L20_2_2_3: ON/OFF ratio per cycle (150 cycles) and mean / median / geometric mean.

Raw (raw_L20_2_2_3/): ID4-3 = SET sweeps (V_G = 4.5 V), ID5-4 = RESET sweeps (V_G = 6.0 V for loops 1-101,
7.0 V for loops 102-150); SET loop n is followed by RESET loop n. Read at |V_TE| = 0.1 V:
  SET sweep:   HRS = forward branch before switching, LRS = return branch
  RESET sweep: LRS = forward branch before switching, HRS = return branch
R includes the transistor channel in series (1T1R), which is why LRS differs between the two sweeps.

Outputs (out_L20_2_2_3/): onoff_per_cycle.txt (with summary statistics at the end)
Run:  python onoff_stats_L20.py
"""
import os
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RAW, OUT = os.path.join(HERE, "raw_L20_2_2_3"), os.path.join(HERE, "out_L20_2_2_3")
os.makedirs(OUT, exist_ok=True)
V_READ = 0.1


def load(fname):
    d = pd.read_csv(os.path.join(RAW, fname), sep="\t", skiprows=[1, 2], na_values=["--"])
    d.columns = [c.replace("_set", "").replace("_reset", "").replace("SMU_G2", "SMU_G") for c in d.columns]
    return d.rename(columns={"Loop Index": "loop", "SMU_TE Voltage": "V", "SMU_TE Current": "I", "SMU_G Voltage": "VG"})


def read_R(branch):
    k = np.argmin(np.abs(branch.V.abs().values - V_READ))
    return abs(branch.V.values[k] / branch.I.values[k])


S, R = load("L20_2_2_3_ID4-3_clean150.txt"), load("L20_2_2_3_ID5-4_clean150.txt")
rows = []
for n in sorted(set(S.loop) & set(R.loop)):
    s, r = S[S.loop == n], R[R.loop == n]
    ks, kr = np.argmax(s.V.values), np.argmin(r.V.values)
    rows.append({"cycle": n, "VG_SET_V": round(s.VG.median(), 2), "VG_RESET_V": round(r.VG.median(), 2),
                 "HRS_SET_ohm": read_R(s.iloc[:ks + 1]), "LRS_SET_ohm": read_R(s.iloc[ks:]),
                 "LRS_RESET_ohm": read_R(r.iloc[:kr + 1]), "HRS_RESET_ohm": read_R(r.iloc[kr:])})
M = pd.DataFrame(rows)
M["ON_OFF_SET"] = M.HRS_SET_ohm / M.LRS_SET_ohm
M["ON_OFF_RESET"] = M.HRS_RESET_ohm / M.LRS_RESET_ohm

summ = []
for col in ("ON_OFF_SET", "ON_OFF_RESET", "HRS_SET_ohm", "LRS_SET_ohm", "LRS_RESET_ohm", "HRS_RESET_ohm"):
    x = M[col]
    summ.append({"quantity": col, "n": len(x), "median": x.median(), "mean": x.mean(),
                 "geometric_mean": 10 ** np.log10(x).mean(), "std": x.std(), "min": x.min(), "max": x.max(),
                 "P10": x.quantile(0.1), "P90": x.quantile(0.9), "skewness": x.skew()})
summ = pd.DataFrame(summ)

with open(os.path.join(OUT, "onoff_per_cycle.txt"), "w") as fh:
    fh.write(f"# 1T1R L20_2_2_3, {len(M)} consecutive cycles, R read at |V_TE| = {V_READ} V\n")
    M.to_csv(fh, sep="\t", index=False, float_format="%.6g")
    fh.write("\n# SUMMARY\n")
    for line in summ.to_csv(sep="\t", index=False, float_format="%.4g").splitlines():
        fh.write("# " + line + "\n")
print(summ.to_string(index=False, float_format="%.4g"))
