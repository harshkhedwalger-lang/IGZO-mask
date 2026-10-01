# IGZO TFT / HfO2 RRAM reticle (HK series) — start here

**Current version: `v52_HK/`** (`v52_HK.oas` + `build_v52.py`, `verify_v52.py`, `v52_HK_report.md`).
Each `vNN_HK/` folder holds the output mask, its generator (reads the previous version) and a change report.
Full background, process stack and verification rules: `v35_HK/CLAUDE.md` — read it, but these later decisions override it:

- **klayout.db only** (`pip install klayout`), never gdstk. Import `klayout.lib` before reading so text PCells resolve.
- Write `.oas` + a `.gds` copy; keep the generator script next to the output; run the full verify suite.
- **Standard pad since v46: 150 x 150 um metal, 140 x 140 um window, 75 um taper** (memristor blocks: 100/90).
- **TFT convention:** gate = L + 2 x 5 um (5 um overlap per side), IGZO 45 um past each gate edge under the
  electrodes, electrode past the IGZO, W = electrode width with IGZO 10 um wider per side, gate exits along W.
- **Text (v52):** every text is a Basic.TEXT PCell, upper case: title mag 100 (70 um), label mag 50 (35 um),
  note mag 30 (21 um); >= 10 um from structures, >= 8 um from other text. Exempt: die title, ResolutionTests artwork.
- Ask the owner before guessing anything process-related.
