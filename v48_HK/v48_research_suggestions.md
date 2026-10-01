# What to add next — literature-backed, prioritized for THIS reticle

**Filter used for every item:** (1) fills a gap the mask doesn't already cover, (2) buildable with
the existing 6-layer flow — M1 | Al2O3 | M2 | HfO2 | [Iso1] | IGZO | M3 | Passivation — with no new
mask, (3) produces a result a reviewer/committee expects for an IGZO-TFT + HfO2-RRAM thesis.

**Already on the mask (so not repeated here):** L/W/overlap/IDT TFT sweeps (PERF_TFT), M1- and
M2-gated TFT arrays, TLM (back-bias), gated VdP + gated Greek cross (Hall-capable), gate-oxide
integrity crosses (Al2O3, HfO2), guarded MIS C-V, CBKR, 1T1R + synaptic 1T1R, memristor area sweep,
gated memristors, stack-split / asymmetric / redundant memristors, 4x4 crossbar, step coverage,
resolution targets. Orphaned (designed, never placed): via chains, Kelvin via, combs, serpentine,
metal vdPs, gated 4-probe TFT, vernier.

---

## Tier 1 — add these first

### 1. Overlay verniers + CD bars for every layer pair  *(small, practical, overdue)*
**Why:** every enclosure rule on this mask uses an *assumed* 2um overlay that has never been
measured; the 8 remaining overlay findings and all pad-window margins hinge on it.
**Build:** box-in-box + comb verniers for M1/M2, M1/Iso1, M2/Iso1, Iso1/IGZO, M1/IGZO, IGZO/M3,
M2/M3, M3/Pass (0.5um vernier step, +/-5um range) + 2/3/5/10um CD bars per layer.
~8 x 250x150um. Standard PCM content ([PCM overview](https://yieldwerx.com/what-is-pcm-test/)).

### 2. Floating-gate synaptic IGZO TFT  *(novel for this mask, zero new layers)*
**Why:** your stack *is* a floating-gate stack: M1 control gate / Al2O3 blocking / **M2 floating
island** / HfO2 tunnel / IGZO channel / M3 S/D. IGZO FG synaptic transistors are an active topic
([Al2O3/ITO/Al2O3 FG-IGZO, J. Phys. D](https://iopscience.iop.org/article/10.1088/1361-6463/ab7bb4);
[ITO-FG IGZO synapse arrays, Adv. Sci. 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC12140291/);
[Al2O3/HfO2 IGZO synaptic TFT, AFM 2026](https://advanced.onlinelibrary.wiley.com/doi/10.1002/adfm.202513449)).
Gives a third, non-filamentary synaptic device to compare against your 1T1R and gated memristors.
**Build:** W/L 50/10um; coupling ratio (FG area / channel area) 0.5, 0.7, 0.85; plus one twin
with the M2 island brought out to a pad (to extract the coupling ratio directly).
**Caveat — your input needed:** whether charge can tunnel through your HfO2 at practical
voltages depends on its thickness; above ~8-10nm expect Fowler-Nordheim at high field only.

### 3. 2T0C IGZO gain cell + storage-node leakage monitor
**Why:** capacitor-less 2-TFT DRAM is the flagship oxide-semiconductor memory result
([imec IEDM 2020, >400s](https://www.imec-int.com/en/press/imec-demonstrates-capacitor-less-igzo-based-dram-cell-400s-retention-time);
[imec, >4.5h, Ioff < 3e-21 A/um](https://www.imec-int.com/en/articles/capacitor-less-igzo-based-dram-cell-excellent-retention-endurance-and-gate-length-scaling);
[ITZO 2T0C >10^4 s](https://pubs.acs.org/doi/10.1021/acsomega.4c08274)). The node-decay method
extracts off-currents 1000x below what DC probing can see — the honest way to report Ioff.
Puts a *volatile* oxide memory next to your *non-volatile* RRAM on one die.
**Build:** write-TFT drain -> M3 -> Iso1 -> M2 gate of the read TFT (HfO2-only gate = large C);
storage-cap variants via read-TFT gate area (x1, x10, x100); write-TFT L = 5, 10, 20um.

### 4. Proper TFT C-V set (DOS + effective mobility), with de-embedding
**Why:** multi-frequency C-V is *the* standard route to IGZO subgap DOS
([IEEE, multifrequency C-V DOS](https://ieeexplore.ieee.org/document/5411783/);
[C-V-based structure-parameter extraction](https://www.researchgate.net/publication/283844346_Extraction_of_structure_parameters_of_a-IGZO_TFTs_based_on_CV_measurement)),
and split C-V gives mobility free of contact resistance — which matters because short-channel
IGZO mobility is routinely overestimated
([gated VdP vs FE mobility, ACS AMI](https://pubs.acs.org/doi/10.1021/acsami.4c14405)).
SPLIT_CV was removed in v44; this is the rigorous replacement.
**Build:** W=L=300um TFT with S+D tied (M1-gated and M2-gated versions) + identical **open
dummy without IGZO** + gate/S-D overlap capacitor, all with the same lead geometry for de-embedding.

### 5. GSG pad sets for pulsed / fast measurements
**Why:** ns-pulse switching and forming overshoot are where RRAM claims are judged; us-pulse I-V
removes charge trapping from TFT mobility — exactly the HfO2 trapping question
([pulse I-V on oxide TFTs](https://pmc.ncbi.nlm.nih.gov/articles/PMC5557951/)).
**Build:** ground-signal-ground pads (100 or 150um pitch — match your probes) on a 1R cell, a
1T1R cell and an L=2-5um TFT, plus open/short structures for de-embedding.

---

## Tier 2 — strong additions

### 6. Parasitic-capacitance ladder for RRAM overshoot
Identical 1R cells with a deliberately added node capacitance (M1/Al2O3/M2 plate on the BE: ~1, 5,
20 pF). Tests the counter-intuitive result that C_par should be *optimised, not minimised*
([Parasitic engineering for RRAM control](https://pmc.ncbi.nlm.nih.gov/articles/PMC6759863/);
[overshoot analysis](https://pubmed.ncbi.nlm.nih.gov/38868495/)). Cheap, and novel for your stack.

### 7. Split buried-gate TFT (M1 segment + M2 segment under one channel)  *(unique to your stack)*
Two gate levels with different EOT (Al2O3+HfO2 vs HfO2) side by side under one IGZO channel ->
independently gated series regions: electrostatic drain extension / field plate for high-Vd and
hot-carrier studies, second-gate Vth tuning. Variants: M2 segment at drain, at source, full-M2
reference. Related dual-gate literature ([dual-gate IGZO reliability, AIP Adv.](https://pubs.aip.org/aip/adv/article/14/11/115122/3321645/Reliability-analysis-under-bias-stress-and);
[hot-carrier TLM-style extraction](https://advanced.onlinelibrary.wiley.com/doi/10.1002/aelm.202500817)).

### 8. Unipolar circuits: inverters + ring oscillators
Diode-load and depletion-load inverters; 5- and 11-stage ring oscillators with output buffer, at
two overlap lengths (2 vs 10um) -> delay vs overlap capacitance
([IGZO ring oscillators](https://www.researchgate.net/publication/341647595_Low-Voltage_High-Speed_Ring_Oscillator_with_a-InGaZnO_TFTs);
[stripe S/D cuts overlap cap, RO 2.5x faster](https://advanced.onlinelibrary.wiley.com/doi/10.1002/aelm.201700550)).

### 9. On-chip heater + thermometer
M1 serpentine heater under one TFT and one 1R cell, M3 4-wire thermometer beside it. Local 25-150 C
steps without a heated chuck: DOS activation energy (Meyer-Neldel), per-device accelerated
retention, self-heating calibration
([self-heating in a-IGZO TFTs](https://www.sciencedirect.com/science/article/abs/pii/S0038110122001654)).

### 10. Low-frequency-noise TFT set
Constant W*L area at 3 aspect ratios + one large low-resistance-lead device; compare M1- vs M2-gated
(HfO2 remote-phonon / trap noise)
([LFN defect profiling in IGZO TFTs, Sci. Rep. 2026](https://www.nature.com/articles/s41598-026-58574-z);
[remote phonon scattering, high-k IGZO](https://link.springer.com/article/10.1007/s11664-023-10576-7)).

---

## Tier 3 — useful, lower urgency

11. **Place the orphaned TS structures** that nothing else duplicates: via_chain_M2_M3, Kelvin_via,
    serpentine_M2, comb_leakage_M2, vdP_GreekCross_M2/M3, gated_4probe_TFT
    ([gated four-probe on IGZO](https://www.researchgate.net/publication/260552279_Analysis_of_temperature-dependent_electrical_characteristics_in_amorphous_In-Ga-Zn-O_thin-film_transistors_using_gated-four-probe_measurements)).
12. **Statistics arrays** — 25 identical reference TFTs and 30-50 identical 1R cells (check whether
    MEM_REDUNDANT already covers the 1R part).
13. **8x8 / 16x16 1R crossbar** with line-resistance monitor lines for V/2 sneak-path and IR-drop
    studies ([IR-drop in RRAM crossbars](https://icsrl.ece.gatech.edu/files/2022/12/Crafton2022ISCAS.pdf);
    [self-rectifying HfO2 memristors](https://link.springer.com/article/10.1007/s40820-025-02035-1)).
14. **Photo-TFT pair** — identical TFTs with and without an ungated IGZO extension, for NBIS and
    optoelectronic-synapse work ([IGZO opto-synaptic transistors](https://pubs.acs.org/doi/abs/10.1021/acsphotonics.4c01809)).
15. **Tunnel-contact / source-gated TFT** — M2 source contacting IGZO *through* the HfO2 (no Iso1),
    after Sporea's Al2O3-interlayer IGZO SGT
    ([Adv. Mater. 2019](https://advanced.onlinelibrary.wiley.com/doi/10.1002/adma.201902551);
    [high-gain SGTs, PNAS](https://pnas.org/content/116/11/4843)). Only if HfO2 is ~nm-thin.

## Two questions that decide items 2 and 15
- What is the HfO2 thickness (and Al2O3)? It determines whether the floating-gate TFT and
  tunnel-contact TFT are realistic.
- Probe card / GSG pitch available (100 or 150um)? It sets the geometry for item 5.
