# TolStack — Mathematical Verification Report

**Scope:** `transforms.py`, `solver.py`, `excel_io.py`, and the MATLAB originals
they port (`Tform.m`, `CoordTform.m`, `extract_HTM_error.m`, `solve_error_comp.m`,
`err_correct2.m`, `nrd.m`, `tag_parse.m`, `check_inputs.m`).
**Method:** symbolic verification (SymPy), closed-form analytic checks, numerical
sweeps, and line-by-line MATLAB↔Python parity review.

---

## 1. What is correct (verified)

These were checked and are sound — no action needed:

- **HTM builders.** `Tform`/`CoordTform` reproduce MATLAB's `makehgtform`
  conventions exactly, including the 3‑2‑1 (Z·Y·X) rotation order and the
  `"o"` (orient‑then‑translate) vs `"p"` (translate‑then‑orient) branches.
- **Rotation extraction — X and Y.** For `R = Rz·Ry·Rx`, `eps_x = atan2(R21,R22)`
  and `eps_y = atan2(-R20, √(R22²+R21²))` are **exact** (verified symbolically;
  residual ≤ 2e‑16 over ±1 rad).
- **Relative‑error model.** `Tre = Tn⁻¹·Tae` and the chain multiplication order
  (`Tn = Tn·CoordTform(Rᵢ)`, left‑to‑right / local‑frame chaining) are correct
  for a serial coordinate chain.
- **Closed‑form agreement.** A single‑segment Abbe case (lever `L`, small Z error
  `θ`) and a two‑segment chain both reproduce the analytic result
  (`dy ≈ L·sinθ`, `dx ≈ L(cosθ−1)`, `eps_z = θ`) to machine precision.
- **Statistics.** `mean(axis=0)` and sample `std(ddof=1)` match MATLAB's `mean`
  and `std` defaults; the 1‑σ = (N‑σ value)/`Nsig` conversion is correct.
- **Monte‑Carlo structure.** Nominal path is held fixed; only the error terms are
  resampled each iteration. Correct.
- **Numeric parity.** Recomputed results match the `RESULT` values stored in the
  workbook across every sheet tested.

---

## 2. Findings, by severity

### 🔴 M1 — `eps_z` extraction is an approximation (coupled), not exact
`extract_HTM_error` computes

```
eps_z = atan2(H[1,0], H[1,1])          # = atan2(R10, R11)
```

The exact Z angle for a `Rz·Ry·Rx` matrix is `atan2(R10, R00)`. Symbolically:

```
eps_z_code = atan2(sinγ·cosβ,  sinα·sinβ·sinγ + cosα·cosγ)   # couples α,β
eps_z_true = γ
```

So `eps_z` is only first‑order correct. Measured error vs the true angle:

| per‑axis error amplitude | max │eps_z − γ│ | % of amplitude |
|---|---|---|
| ±0.01 rad | 4.9e‑7 | 0.005 % |
| ±0.05 rad | 6.0e‑5 | 0.12 % |
| ±0.1 rad  | 4.9e‑4 | 0.49 % |
| ±0.3 rad  | 1.4e‑2 | 4.6 % |
| ±0.5 rad  | 7.4e‑2 | 15 % |
| ±1.0 rad  | 1.1e0  | >100 % (invalid) |

**In practice it's applied only to the *relative error* transform, which is
small, so current results are fine.** But it's fragile: any workbook with a
per‑segment angular error beyond ~0.1 rad silently loses accuracy on the Z term.

**Recommended fix (exact, zero cost, keeps X/Y unchanged):**
```python
eps_z = np.arctan2(H[1, 0], H[0, 0])   # was H[1, 1]
```
Apply the same one‑line change to `extract_HTM_error.m` to keep MATLAB↔Python
parity. This is strictly more correct and only changes outputs in the regime
where the old formula was already wrong.

### 🟠 M2 — Silent NaN propagation from malformed input
`tag_parse` pads short rows with `"NaN"` and keeps rows that are partly numeric.
A row with a blank/typo (e.g. `R = 1, 0, 0, 0, 0, <blank>` or `0.1, abc, …`)
produces a `NaN` that flows through the whole Monte Carlo and yields `NaN`
results with **no error or warning**. Verified.

**Recommendation:** after parsing, validate that `R`, `Re`, `C`, `Cv` are fully
finite; if not, raise a clear message naming the offending tag/row instead of
solving. (This also protects the eventual open‑source users from confusing
"all‑NaN result" reports.)

### 🟠 M3 — Degenerate configuration values are unguarded
- `N_SAMPLES = 1` → `std(ddof=1)` divides by zero → σ = `NaN` (verified).
- `N_SAMPLES ≤ 0` → empty error array → `NaN` statistics.
- `N_SIGMA = 0` → `Re/Nsig` → `inf`/`NaN` (verified).

`check_inputs` supplies defaults only when a value is *missing*, not when it is
present‑but‑invalid.

**Recommendation:** enforce `N_SAMPLES ≥ 2` and `N_SIGMA > 0` with explicit
messages.

### 🟠 M4 — Compensator gating logic is fragile and Python/MATLAB diverge
The branch that decides whether to compensate is:

```python
if not np.all(C):     # Python
% if ~all(C)          % MATLAB
```

Behavior table (True = run compensation):

| C | MATLAB | Python |
|---|---|---|
| all‑zero 1×6 | True | True |
| `[0,0,0,0,0,0.001]` (typical) | True | True |
| **fully non‑zero 1×6** | **False** | **False** |
| 2‑row mixed | True | True |
| 2‑row, one column non‑zero in all rows | **True** | **False** ← diverge |

Two problems: (a) a **fully‑populated corrector row is skipped entirely** (no
compensation applied even though a corrector was given); (b) MATLAB's matrix
`all()` semantics differ from Python's scalar `np.all()`, so the two
implementations disagree on the multi‑row case.

**Recommendation:** replace the gate with the intended meaning — "compensate if
any corrector is present":
```python
if np.any(C != 0):
```
and mirror it in MATLAB (`if any(C(:))`). Per‑row all‑zero skipping already
exists inside `err_correct2`, so this is safe.

### 🟡 M5 — `DISTRIBUTION` input is read but never used
The workbook advertises `DISTRIBUTION = N (Normal) / U (Uniform)`, and the value
is parsed into `input_distribution`, but sampling is **always Gaussian**
(`nrd → np.random.randn`). Uniform is silently ignored (same in MATLAB).

**Recommendation:** either implement the uniform branch in `nrd`
(e.g. `±√3·σ` uniform to match variance) or remove the column/label so the tool
doesn't promise a mode it doesn't have.

### 🟡 M6 — Numeric `NAME`/`DISTRIBUTION` cells can crash `check_inputs`
If a `NAME` (or `DISTRIBUTION`) cell holds a number, `tag_parse` returns a NumPy
array, and `if not s.Name:` then raises *"truth value of an array is ambiguous."*

**Recommendation:** coerce these text tags to `str` at parse time.

### 🟡 M7 — Excel read/write target the workbook inconsistently
`read_active_excel` reads from `excel.Selection` (whatever is active), but
`write_results` writes to `excel.Workbooks(1).ActiveSheet`. If the intended
workbook isn't the first one open, or the active sheet changes between read and
write, results land in the wrong place.

**Recommendation:** capture the worksheet/workbook object from the *selection*
during the read and write back to that same sheet.

### 🟡 M8 — One‑sided `mu + N·sigma` summary
`uplusNsigma = mu + Nsig·sigma` is a single upper bound. For an error with a
non‑zero or asymmetric mean, this can under‑represent the worst case (it ignores
the `mu − N·sigma` excursion). Fine for zero‑mean symmetric inputs (the common
case), but worth stating.

**Recommendation:** consider reporting `|mu| + N·sigma`, or both bounds, and
document the convention.

### 🟢 Minor / parity notes
- **MATLAB `check_inputs` size checks are effectively no‑ops.**
  `if size(R) ~= size(Re)` only trips when *both* dimensions differ, and
  `size(C,1) ~= size(Cv)` compares a scalar to a 1×2 vector. The Python port is
  actually more correct; align the two.
- **Gimbal lock:** at `eps_y = ±90°` the Z/X split is undefined. Unreachable with
  small errors, but note the domain limit.
- **Duplicate text tags:** only the last match of a text tag (e.g. `NAME`) is
  kept. Harmless, but undefined if a sheet lists two.
- **Histogram units** are hard‑labeled `mm`/`rad`; some sheets use `µm`/`mdeg`.
  Cosmetic.

---

## 3. Suggested priority for open‑source hardening
1. **M1** — one‑line exact `eps_z` fix (correctness).
2. **M2 / M3** — input validation + degenerate guards (prevents silent `NaN`).
3. **M4** — fix compensator gate and unify with MATLAB (correctness + parity).
4. **M6 / M7** — robustness of parsing and Excel write‑back.
5. **M5 / M8** — implement or remove the Uniform option; document the summary
   statistic.

All core transform/propagation math is correct; the above are edge‑case
robustness and one bounded approximation, not errors in the central algorithm.

---

## 4. Fixes applied (this revision)

Implemented in `transforms.py` and `solver.py`, each verified numerically:

| Item | Fix | Verification |
|---|---|---|
| **M1** | `eps_z` now uses the exact ZYX inverse `atan2(H[1,0], H[0,0])`. Added `rotation_vector_error()` (SO(3) log map) as a robust, order‑independent option. | Round‑trip error ≤ 2e‑16 at all angles (was up to 2.8 rad). Impact on existing small‑error sheets ≤ 6e‑5 rad — results unchanged within MC noise. |
| **M2** | `check_inputs` rejects any `R/Re/C/Cv` block containing blank/non‑numeric (`NaN`) cells, naming the tag. | Verified: NaN in any block → invalid with message. |
| **M3** | Guards added: `N_SAMPLES ≥ 2`, `N_SIGMA > 0`, unrecognized `DISTRIBUTION` → Normal + note. | Verified each guard trips correctly; valid input passes clean. |
| **M4** | Compensation gate changed to `if np.any(C != 0)` ("any corrector present"), fixing the skipped fully‑populated corrector and the MATLAB/Python divergence. | Verified truth table; typical correctors unchanged. |
| **M5** | `draw_error(limits, nsig, distribution)` added. **Normal** = `N(0, Re/nsig)` (bit‑identical to the old `nrd`, so existing sheets are unchanged); **Uniform** = `U(−Re, +Re)` (full tolerance band). Wired through `tol_stack_solve` using the sheet's `DISTRIBUTION` tag. | Normal reproduces legacy `nrd` exactly (same seed); Uniform fills ±Re with σ = Re/√3; end‑to‑end Uniform run gives the expected wider band. |
| **M6** | `NAME`/`DISTRIBUTION` coerced to `str` at parse time. | No longer raises on a numeric label. |

### Still open (recommended, not yet changed)
- **M7** — Excel read (active selection) vs write (`Workbooks(1).ActiveSheet`) can target different workbooks; capture the sheet from the selection and write back to it.
- **M8** — `mu + N·sigma` is one‑sided; consider `|mu| + N·sigma` or reporting both bounds, and document the convention.
- **MATLAB parity** — apply the same M1 (`eps_z`) and M4 (gate) fixes to `extract_HTM_error.m` and `solve_error_comp.m`, and add the M2/M3 guards, so the `.m` sources and the Python port stay in sync for the open‑source release.
