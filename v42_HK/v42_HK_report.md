# v42_HK — change report (from v41_HK)

## What changed
**`1T1R` moved up by 580 µm** — bounded by the real clearance to `SYN_1T1R`, which sits directly above it
(their X-ranges overlap over most of `1T1R`'s width) and was not part of this request. Original gap was
700 µm; moved up leaving 120 µm clearance. Verified clear of every other block and every alignment mark
before committing.

## What was NOT done, and why (real numbers, not a guess)
`STEP_COVERAGE`, `XBAR_4X4`, `SPLIT_CV`, `PERF_TFT` were **not** moved down. A real space check shows there
is nowhere for them to land without displacing a block that wasn't part of this request:

| check | result |
|---|---|
| `PERF_TFT` needs | 5032 × 1706 µm |
| clearance between `PERF_TFT` and `Memristors` today | 1501 µm — `Memristors` already occupies that column up to within 1501 µm of `PERF_TFT`'s current position |
| space freed below the new `1T1R` position | 1775 µm tall, but bounded above by `CBKR_Structures`/`MEM_HIGH_VALUE`, not open all the way to `TestStructures` |

The "bottom" of this die is already filled by `Memristors`, `MEM_REDUNDANT`, `MEM_HIGH_VALUE`, `MEM_ASYM`,
`TestStructures`, `CBKR_Structures`, `MEM_STACK_SPLIT`. Moving the four blocks down as asked would require
also relocating one or more of those — out of scope for this pass without confirmation.

## Verification (`v42_build_log.txt`)
| check | result |
|---|---|
| connectivity / fabricability | 0 findings |
| overlay rules | 8, same pre-existing `MEM_HIGH_VALUE` findings, unchanged |
| structure overlap | 63 µm², same pre-existing legacy stray dash near CBKR |
| `1T1R` gaps to neighbours | none < 60 µm |
| alignment-mark keep-out | 0 violations |
| DRC 2 µm | TOP unchanged pattern (25/61) |
| cells changed | `TOP` only |
