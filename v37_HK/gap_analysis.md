# What a standard IGZO-TFT / RRAM test reticle carries that this mask still lacks
Prioritised gap list, v37_HK. Sources at the bottom; my own judgement is marked as such.

## P0 — you can be asked for these at review and currently cannot answer

| # | missing | why it matters | cost |
|---|---|---|---|
| 1 | **Gated van der Pauw / gated Hall bar at short L** | Published result (ACS AMI 2024): field-effect mobility from short-channel IGZO TFTs is **systematically over-estimated**; the gated van der Pauw structure is the accepted fix because it removes contact resistance from the mobility extraction. You have `gated_vanderPauw`, but not at the short L where the error appears, and no Hall bar → no independent carrier density, so µ_Hall vs µ_FE cannot be separated. Any mobility number you publish from L = 2–10 µm devices is challengeable without it. | ~2 cells + 1 Hall bar |
| 2 | **Device-count statistics per condition** | RRAM variability work is judged on distributions, not exemplars: in-line RRAM variability studies report forming-voltage, LRS and HRS distributions over large device populations, and 1T1R endurance/variability is characterised across a wide compliance range (µA → ~500 µA). Your new SYN block has **1 device per (driver, junction)** — enough for a trend, not for a σ claim. | 4–8× replication of 2–3 chosen cells |
| 3 | **On-chip series/parasitic control for forming** | Current overshoot at forming — driven by parasitic capacitance of the line between compliance element and device — is a recognised source of RRAM variability; the standard mitigation is putting the compliance element as close as possible (1T1R) and minimising line capacitance. You have 1T1R (good) but **no structure that measures the parasitic** (no short/open/line-capacitance de-embed next to a memristor), so you cannot prove your overshoot is controlled or compare 1R vs 1T1R fairly. | 1 open + 1 short + 1 line-cap cell |
| 4 | **Kelvin (4-wire) on the memristor itself** | Your memristor LRS can reach the 100 Ω–1 kΩ range where probe + line resistance is not negligible; 2-wire LRS is then wrong. CBKR is the standard structure for low contact resistance and you already use it for contacts, but not on the junction. | 2 cells |

## P1 — expected in a mature mask, absent here

| # | missing | why |
|---|---|---|
| 5 | **NBIS / PBTS stability pair with light shield** | Oxide-TFT reliability is reported as PBTS / NBTS / PBITS / NBITS; NBIS is *the* known a-IGZO weakness (ΔV_th ~8.5 V in 1000 s for an unoptimised active layer, ~3.2 V optimised). With Metal_4 removed you no longer have a shield layer — the only remaining option is an M1 shield under the channel, i.e. **shield-from-below plus a bare twin**. Without the pair you cannot claim stability at all. |
| 6 | **Wafer-scale uniformity replicas** | A 14 mm die will have sputter/ALD gradients. Standard practice: repeat a small device set at die corners + centre so process gradient can be separated from device variance. You have none — every structure exists at exactly one location. |
| 7 | **Lift-off yield monitor (comb/serpentine per metal)** | Comb-serpentine short/open structures are the classic PCM yield monitor. With lift-off at 2 µm this is your most likely yield killer and you have no quantitative monitor for it. |
| 8 | **Sheet-resistance van der Pauw per conducting layer** | Greek-cross vdP is the standard sheet-resistance PCM structure. You have it for gated IGZO only — **no R_sheet for M1, M2, M3**, so you cannot separate line resistance from device resistance, or normalise TLM. |
| 9 | **Cross-bridge Kelvin + CBKR with end contact → transfer length** | You removed ungated CBKR correctly, but the gated version does not give L_T without an end-contact variant. |

## P2 — worth having, lower urgency
10. **1T1R endurance/pulse cell with low-inductance layout** (nanosecond switching work uses dedicated 1T1R test vehicles); your manual pads limit you to ~µs, so this is only worth it if you get an RF/pulse setup.
11. **Line-resistance / IR-drop monitor for array word and bit lines** — needed before any array-level claim.
12. **Temperature: heater + 4-wire RTD** next to a memristor and a TFT → activation energy, conduction mechanism. Referees ask for mechanism.
13. **Dedicated overlay verniers per layer pair** — you have litho/CD artwork (63/0) but no electrical overlay structure; overlay is currently an assumption (mkaudit is still running on OVL = 2 µm *assumed*).

## Honest notes
- Items 1, 5, 7, 8, 12 I had already flagged from device physics in earlier sessions; the literature search confirms 1, 2, 3 and 5 as standard expectations rather than my preference.
- I could not retrieve two sources (ACS full text and one arXiv PDF) — the mobility-overestimation and variability-statistics points rest on the abstract/summary text returned by search, not on the full papers. Worth you checking the ACS paper directly before I lay out structure #1.
- Items 2 and 6 cost only replication, not new device design — cheapest real credibility gain on this list.

## Sources
- [Addressing Mobility Overestimation in Short-Channel IGZO TFTs Using the Gated Van der Pauw Method, ACS Appl. Mater. Interfaces](https://pubs.acs.org/doi/10.1021/acsami.4c14405)
- [Parasitic engineering for RRAM control (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC6759863/)
- [In-Line-Test of Variability and Bit-Error-Rate of HfOx-Based Resistive Memory (arXiv:1509.00070)](https://arxiv.org/pdf/1509.00070)
- [Compliance-Free Pulse Forming of Filamentary RRAM (NIST)](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=921335)
- [Advanced 1T1R test vehicle for RRAM nanosecond-range switching-time resolution](https://www.researchgate.net/publication/304256311_Advanced_1T1R_test_vehicle_for_RRAM_nanosecond-range_switching-time_resolution_and_reliability_assessment)
- [Negative bias illumination stress stability of dual-active-layer a-IGZO TFT, phys. status solidi (a)](https://onlinelibrary.wiley.com/doi/abs/10.1002/pssa.201533052)
- [Electrical instabilities of a-IGZO TFTs under bias and illumination stress, ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S002627142300286X)
- [Cross-bridge Kelvin resistor (CBKR) structures for measurement of low contact resistances](https://www.researchgate.net/publication/228608938_Cross-bridge_Kelvin_resistor_CBKR_structures_for_measurement_of_low_contact_resistances)
- [Simulation and Analysis of Analog Circuit and PCM (Process Control Monitor) Test Structures](https://d-nb.info/1212627229/34)
