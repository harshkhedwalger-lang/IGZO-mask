"""Raw measured points behind the ON/OFF statistics (median / mean) at |V| = 0.1 V.

For every selected cycle, writes the exact V and I the HRS and LRS values were read from, with the line
number in the original raw file, so every ratio can be checked by hand:
    R = |V / I|,  ON/OFF = R_HRS / R_LRS
SET sweep (+0.1 V): HRS = forward branch before switching, LRS = return branch after switching.
RESET sweep (-0.1 V): LRS = forward branch before switching, HRS = return branch after switching.

Outputs (out/): onoff_raw_<set>.txt  (one row per cycle per sweep, summary statistics at the end)
Run after stable50.py and analyze_best50.py:   python onoff_raw_table.py
"""
import os
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RAW, OUT = os.path.join(HERE, "raw"), os.path.join(HERE, "out")
FILES = {"2_21": ("2_21_ID3_set.txt", "2_21_ID4_reset.txt"),
         "TE_SET": ("TE_SET_ID3_set.txt", "TE_SET_ID4_reset.txt")}
SETS = {"stable50": ("stable50_metrics.txt", "sel_no"), "best50": ("best50_metrics.txt", "best_no")}
V_READ, V_TOL, CC = 0.1, 0.01, 110e-6
FIRST_DATA_LINE = 4  # raw files: line 1 header, line 2 units, line 3 blank


def load(fname):
    d = pd.read_csv(os.path.join(RAW, fname), sep="\t", skiprows=[1, 2], na_values=["--"])
    d = d.rename(columns=lambda c: c.replace("_set", "").replace("_reset", ""))
    d = d.rename(columns={"Loop2 Index": "loop", "SMU_TE Voltage": "V", "SMU_TE Current": "I"})
    d["file_line"] = d.index + FIRST_DATA_LINE
    return d[["loop", "V", "I", "file_line"]]


def pick(branch):
    """Measured point on this branch closest to |V| = V_READ (same rule as the plots)."""
    k = np.argmin(np.abs(branch.V.abs().values - V_READ))
    p = branch.iloc[k]
    ok = abs(abs(p.V) - V_READ) <= V_TOL and p.I != 0 and abs(p.I) < 0.95 * CC
    return p, ok


data = {run: tuple(load(f) for f in fs) for run, fs in FILES.items()}

for name, (mfile, idx) in SETS.items():
    sel = pd.read_csv(os.path.join(OUT, mfile), sep="\t")
    rows = []
    for _, b in sel.iterrows():
        S, R = data[b.run]
        s, r = S[S.loop == b.cycle], R[R.loop == b.cycle]
        ks, kr = int(np.argmax(s.V.values)), int(np.argmin(r.V.values))
        for sweep, fname, hrs_br, lrs_br in (
                ("SET (+0.1 V)", FILES[b.run][0], s.iloc[:ks + 1], s.iloc[ks:]),
                ("RESET (-0.1 V)", FILES[b.run][1], r.iloc[kr:], r.iloc[:kr + 1])):
            h, hok = pick(hrs_br)
            l, lok = pick(lrs_br)
            R_h, R_l = abs(h.V / h.I), abs(l.V / l.I)
            rows.append({idx: b[idx], "run": b.run, "cycle": b.cycle, "sweep": sweep, "raw_file": fname,
                         "HRS_line": int(h.file_line), "HRS_V_V": h.V, "HRS_I_A": h.I,
                         "LRS_line": int(l.file_line), "LRS_V_V": l.V, "LRS_I_A": l.I,
                         "R_HRS_ohm": R_h, "R_LRS_ohm": R_l, "ON_OFF": R_h / R_l, "valid_read": hok and lok})
    T = pd.DataFrame(rows)

    out = os.path.join(OUT, f"onoff_raw_{name}.txt")
    with open(out, "w") as fh:
        fh.write(f"# Raw points behind the ON/OFF ratio, {name} set, read at |V| = {V_READ} V, CC = 0.1 mA\n")
        fh.write("# R = |V/I| from the measured point; ON/OFF = R_HRS / R_LRS; HRS_line / LRS_line = line in raw_file\n")
        T.to_csv(fh, sep="\t", index=False, float_format="%.6e")
        fh.write("\n# SUMMARY (ON/OFF over the cycles of each sweep)\n")
        fh.write("# sweep\tn\tmedian\tmean\tgeometric_mean\tmin\tmax\tstd\n")
        for sw, g in T.groupby("sweep", sort=False):
            x = g.ON_OFF
            fh.write(f"# {sw}\t{len(x)}\t{x.median():.1f}\t{x.mean():.1f}\t{10 ** np.log10(x).mean():.1f}"
                     f"\t{x.min():.1f}\t{x.max():.1f}\t{x.std():.1f}\n")
    print(name, "invalid reads:", int((~T.valid_read).sum()))
    print(T.groupby("sweep", sort=False).ON_OFF.agg(["count", "median", "mean", "min", "max"]).round(1).to_string())
