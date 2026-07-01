"""
solver.py
Core TolStack simulation logic.

Direct Python/NumPy port of the MATLAB functions:
    STACKRANGE.m, tag_parse.m, fetchstack.m, check_inputs.m, nrd.m,
    solve_error_comp.m, err_correct2.m, TolStackSolve.m

The Monte-Carlo model propagates 6-DOF error through a chain of HTMs and
reports mu + N*sigma of the relative error at the end of the vector path.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import numpy as np

from transforms import CoordTform, extract_HTM_error


# ---------------------------------------------------------------------------
# STACKRANGE  (port of STACKRANGE.m)
# ---------------------------------------------------------------------------
# Tag name -> number of value cells to read to the right of the tag.
DEFAULT_TAGS: List[Tuple[str, int]] = [
    ("R", 6),
    ("Re", 6),
    ("C", 6),
    ("Cv", 6),
    ("N_SAMPLES", 1),
    ("N_SIGMA", 1),
    ("RESULT", 6),
    ("PLOT", 1),
    ("NAME", 1),
    ("DISTRIBUTION", 1),
]


@dataclass
class StackRange:
    """Container for all Excel inputs and simulation results."""

    Name: str = ""
    R: Optional[np.ndarray] = None
    Re: Optional[np.ndarray] = None
    C: Optional[np.ndarray] = None
    Cv: Optional[np.ndarray] = None
    N: Optional[int] = None
    Nsig: Optional[float] = None
    Result: Optional[Tuple[int, int]] = None
    Plot: int = 0
    invalid_stack: int = 0
    input_distribution: str = ""
    tags: List[Tuple[str, int]] = field(default_factory=lambda: list(DEFAULT_TAGS))

    # Results
    mu: Optional[np.ndarray] = None
    sigma: Optional[np.ndarray] = None
    uplusNsigma: Optional[np.ndarray] = None
    T_uplusNsigma: Optional[np.ndarray] = None
    Error: Optional[np.ndarray] = None
    Tn_list: Optional[List[np.ndarray]] = None
    Tc_list: Optional[List[np.ndarray]] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _str2double(s: str) -> float:
    """MATLAB-like str2double: numeric string -> float, else NaN."""
    try:
        return float(s)
    except (ValueError, TypeError):
        return math.nan


def tag_parse(data: List[List[str]], tag: str, tag_length: int):
    """Find `tag` in the string grid and grab `tag_length` cells to its right.

    Returns (output, idx):
      output : np.ndarray (n_matches x tag_length) for numeric tags,
               str for a text tag, or None if the tag is not found.
      idx    : list of 1-based [row, col] positions where the tag matched.
    """
    rows = len(data)
    numeric_rows: List[List[float]] = []
    string_value: Optional[str] = None
    idx: List[List[int]] = []

    for r in range(rows):
        cols = len(data[r])
        for c in range(cols):
            value = data[r][c]
            if not isinstance(value, str):
                continue
            if value != tag:
                continue

            idx.append([r + 1, c + 1])  # store 1-based index (MATLAB parity)

            # Grab the tag_length cells to the right (pad with "NaN" if short).
            raw = []
            for k in range(1, tag_length + 1):
                raw.append(data[r][c + k] if (c + k) < cols else "NaN")

            parsed = [_str2double(x) for x in raw]

            if all(math.isnan(p) for p in parsed):
                # All non-numeric -> treat as a string input (length-1 tags).
                string_value = raw[0]
            else:
                numeric_rows.append(parsed)

    if string_value is not None:
        return string_value, idx
    if numeric_rows:
        return np.array(numeric_rows, dtype=float), idx
    return None, idx


def fetchstack(s: StackRange) -> StackRange:
    """Read the active Excel selection and parse it into the StackRange."""
    from excel_io import read_active_excel

    data, _address, startcell = read_active_excel()

    parsed = {}
    idxs = {}
    for name, length in s.tags:
        parsed[name], idxs[name] = tag_parse(data, name, length)

    s.R = parsed["R"]
    s.Re = parsed["Re"]
    s.C = parsed["C"]
    s.Cv = parsed["Cv"]

    s.N = None if parsed["N_SAMPLES"] is None else int(np.ravel(parsed["N_SAMPLES"])[0])
    s.Nsig = None if parsed["N_SIGMA"] is None else float(np.ravel(parsed["N_SIGMA"])[0])

    # RESULT: absolute cell = start cell + (index within selection) - 1
    if idxs["RESULT"]:
        ir, ic = idxs["RESULT"][0]
        s.Result = (startcell[0] + ir - 1, startcell[1] + ic - 1)
    else:
        s.Result = None

    s.Plot = 0 if parsed["PLOT"] is None else int(np.ravel(parsed["PLOT"])[0])
    s.Name = parsed["NAME"] if parsed["NAME"] is not None else ""
    s.input_distribution = parsed["DISTRIBUTION"] if parsed["DISTRIBUTION"] is not None else ""

    return s


def check_inputs(s: StackRange) -> StackRange:
    """Validate inputs, apply defaults. Port of check_inputs.m.

    Returns the (possibly modified) StackRange with `invalid_stack` set and a
    `messages` attribute listing any notes (attached dynamically).
    """
    messages: List[str] = []

    if s.R is None or np.size(s.R) == 0:
        s.invalid_stack = 1
        messages.append("Required Input Missing: R")
    if s.Re is None or np.size(s.Re) == 0:
        s.invalid_stack = 1
        messages.append("Required Input Missing: Re")
    if s.C is None or np.size(s.C) == 0:
        messages.append("Optional Input Missing: C Will Not Be Used")
        s.C = np.zeros((1, 6))
    if s.Cv is None or np.size(s.Cv) == 0:
        messages.append("Optional Input Missing: Cv Will Not Be Used")
        s.Cv = np.zeros((1, 6))
    if s.N is None:
        messages.append("Optional Input Missing: N = 1000 Default Will Be Used")
        s.N = 1000
    if s.Nsig is None:
        messages.append("Optional Input Missing: Nsig = 3 Default Will Be Used")
        s.Nsig = 3
    if not s.input_distribution:
        messages.append("Optional Input Missing: Normal Distribution Default Will Be Used")
        s.input_distribution = "Normal"
    if s.Result is None:
        s.invalid_stack = 1
        messages.append("Required Input Missing: RESULT")
    if not s.Name:
        messages.append("Optional Input Missing: Stack Name, T1T2 Will be Used")
        s.Name = "T1T2"

    # R and Re must be the same size.
    if s.R is not None and s.Re is not None and np.shape(s.R) != np.shape(s.Re):
        messages.append("Error: R and Re Size Mismatch")
        s.invalid_stack = 1

    # Same number of correctors as corrector vectors.
    if s.C is not None and s.Cv is not None and np.shape(s.C)[0] != np.shape(s.Cv)[0]:
        messages.append("Error: Different Number of C and Cv Rows")
        s.invalid_stack = 1

    s.messages = messages  # type: ignore[attr-defined]
    return s


def nrd(mu: np.ndarray, sigma: np.ndarray) -> np.ndarray:
    """Normally distributed random values, element-wise. Port of nrd.m."""
    mu = np.asarray(mu, dtype=float)
    sigma = np.asarray(sigma, dtype=float)
    if mu.shape == sigma.shape:
        return np.random.randn(*sigma.shape) * sigma + mu
    if sigma.size == 1:
        return np.random.randn(*mu.shape) * float(sigma) + mu
    # Size mismatch: MATLAB returns zeros in this case.
    return np.zeros(mu.shape)


def err_correct2(Tre, Tae, Tn, C, Cv):
    """Apply compensators by replacement. Port of err_correct2.m."""
    C = np.atleast_2d(np.asarray(C, dtype=float))
    Cv = np.atleast_2d(np.asarray(Cv, dtype=float))
    rowC = C.shape[0]
    for j in range(rowC):
        if np.all(C[j, :] == 0):
            continue  # No corrector on this row -> skip.
        Ere = extract_HTM_error(Tre)
        CD = np.zeros(6)
        for i in range(6):
            CD[i] = 0.0 if C[j, i] == 0 else C[j, i] - Ere[i]
        Tvc = CoordTform(-Cv[j, :], "o")            # transform to compensator
        Tcd = CoordTform(CD, "o")                   # transform to compensate by
        Tcae = Tae @ (np.linalg.solve(Tvc, (Tcd @ Tvc)))
        Tcre = np.linalg.solve(Tn, Tcae)
        Ecre = extract_HTM_error(Tcre)
        Tre = CoordTform(Ecre, "o")
    return Tre


def solve_error_comp(Rn, Re, C, Vc):
    """Solve relative 6-DOF error along a vector path. Port of solve_error_comp.m.

    Returns (Ec, Tn, Tae, Tre, Tc, Tn_list, Tc_list).
    """
    Rn = np.atleast_2d(np.asarray(Rn, dtype=float))
    Re = np.atleast_2d(np.asarray(Re, dtype=float))
    C = np.atleast_2d(np.asarray(C, dtype=float))

    Tn = np.eye(4)
    Tae = np.eye(4)
    n = Rn.shape[0]
    Tn_list: List[np.ndarray] = [None] * n
    Tc_list: List[np.ndarray] = [None] * n

    Ec = np.zeros(6)
    Tre = np.eye(4)
    Tc = np.eye(4)

    for i in range(n):
        # Nominal position transform (left-to-right multiplication).
        Tn = Tn @ CoordTform(Rn[i, :], "o")
        Tn_list[i] = Tn

        # Absolute position with error transform.
        Tae = Tae @ CoordTform(Re[i, :], "o") @ CoordTform(Rn[i, :], "o")

        # Relative error transform.
        Tre = np.linalg.solve(Tn, Tae)

        if not np.all(C):  # a zero anywhere in C -> compensation branch
            Trec = err_correct2(Tre, Tae, Tn, C, Vc)
            Ec = extract_HTM_error(Trec)  # (loop over C rows collapses to last)
            Tc = CoordTform(Ec, "o")
        else:
            Ec = extract_HTM_error(Tre)
            Tc = Tre

        Tc_list[i] = Tc

    return Ec, Tn, Tae, Tre, Tc, Tn_list, Tc_list


def tol_stack_solve(s: Optional[StackRange] = None, log=None):
    """Full solve pipeline. Port of TolStackSolve.m.

    Parameters
    ----------
    s   : StackRange (a fresh one is created if None)
    log : optional callable(str) for status messages

    Returns the populated StackRange, or None if inputs are invalid.
    Plotting and writing results back to Excel are handled by the caller
    (see app.py) so this function stays UI/IO-light and testable.
    """
    if s is None:
        s = StackRange()

    def emit(msg):
        if log:
            log(msg)

    # Fetch + verify.
    s = fetchstack(s)
    s = check_inputs(s)
    for m in getattr(s, "messages", []):
        emit(m)

    if s.invalid_stack:
        emit("INVALID INPUTS")
        return None

    # 1-sigma error from N-sigma input.
    Re_ns = np.asarray(s.Re, dtype=float) / s.Nsig

    # Monte-Carlo.
    emit(f"Solving '{s.Name}': N={s.N} samples, {s.input_distribution} distribution...")
    error = np.zeros((s.N, 6))
    Tn_list = None
    Tc_list = None
    zeros_mu = np.zeros_like(Re_ns)
    for i in range(s.N):
        e, _, _, _, _, Tn_list, Tc_list = solve_error_comp(
            s.R, nrd(zeros_mu, Re_ns), s.C, s.Cv
        )
        error[i, :] = e

    s.Error = error
    s.Tn_list = Tn_list
    s.Tc_list = Tc_list

    # Statistics (sample std, ddof=1, matching MATLAB std default).
    s.mu = np.mean(error, axis=0)
    s.sigma = np.std(error, axis=0, ddof=1)
    s.uplusNsigma = s.mu + s.Nsig * s.sigma
    s.T_uplusNsigma = CoordTform(s.uplusNsigma, "p")

    emit("Montecarlo complete.")
    return s
