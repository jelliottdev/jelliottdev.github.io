"""Independent exact small-field oracle and source arithmetic check."""
import hashlib
import json
import math
from fractions import Fraction as F
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
plan = json.loads((HERE / "plan.json").read_text())
result = json.loads((HERE / "results.json").read_text())

for item in plan["inputs"]:
    assert hashlib.sha256((ROOT / item["path"]).read_bytes()).hexdigest() == item["sha256"]
assert hashlib.sha256((HERE / "plan.json").read_bytes()).hexdigest() == result["plan_sha256"]


def skip_oracle(n, s, previous, plain):
    # Exhaust every key and the two branches of a rejection coin in one draw.
    # Normalize the accepted masses by 1 minus the independent loop mass.
    mass = [F(0)] * n
    loop = F(0)
    for key in range(n):
        candidate = (plain + key) % n
        weight = F(1, n)
        if candidate == previous:
            mass[candidate] += weight * (1 - s)
            loop += weight * s
        else:
            mass[candidate] += weight
    assert loop < 1
    return tuple(v / (1 - loop) for v in mass), loop


def rewrite_oracle(n, t, previous, plain):
    mass = [F(0)] * n
    for key in range(n):
        candidate = (plain + key) % n
        if candidate == previous:
            mass[candidate] += F(1, n) * (1 - t)
            for redraw in range(n):
                mass[redraw] += F(1, n) * t / n
        else:
            mass[candidate] += F(1, n)
    return tuple(mass)


# Nontrivial exact finite-field control: both filters yield the same visible
# distribution for every previous symbol and every plaintext symbol.
n, s, t = 3, F(1, 2), F(3, 5)
for previous in range(n):
    expected = tuple(F(1, 5) if out == previous else F(2, 5) for out in range(n))
    for plain in range(n):
        law, loop = skip_oracle(n, s, previous, plain)
        assert loop == F(1, 6)
        assert law == expected
        assert rewrite_oracle(n, t, previous, plain) == expected

# Edge control: zero suppression returns exactly uniform ciphertext.
for previous in range(n):
    for plain in range(n):
        assert skip_oracle(n, F(0), previous, plain)[0] == (F(1, 3),) * n
        assert rewrite_oracle(n, F(0), previous, plain) == (F(1, 3),) * n

N = 29
r = F(86, 12955)
fitted_skip = (1 - N * r) / (1 - r)
fitted_rewrite = N * (1 - N * r) / (N - 1)
repeat_skip = (1 - fitted_skip) / (N - fitted_skip)
repeat_rewrite = (1 - fitted_rewrite) / N + fitted_rewrite / N**2
other_skip = 1 / (N - fitted_skip)
other_rewrite = F(1, N) + fitted_rewrite / N**2
assert repeat_skip == repeat_rewrite == r
assert other_skip == other_rewrite == (1-r)/(N-1)
assert math.isclose(float(fitted_skip), result["skip_s_fitted"], abs_tol=1e-14)
assert math.isclose(float(fitted_rewrite), result["rewrite_s_fitted"], abs_tol=1e-14)
assert math.isclose(float(repeat_skip), result["repeat_probability"], abs_tol=1e-14)
assert math.isclose(float(other_skip), result["each_other_symbol_probability"], abs_tol=1e-14)
q = fitted_skip / N
assert math.isclose(float(F(12955) * q/(1-q)), result["expected_extra_draws"], abs_tol=1e-10)

source_budget = json.loads((HERE / "source/c_budget.json").read_text())
source_drift = json.loads((HERE / "source/b_drawcount.json").read_text())
source_s = F(8129, 10000)
assert abs(float((1-source_s)/(N-source_s)) - source_budget["acceptance_channel"]["closed_form_residual_rate"]) < 1e-14
assert abs(float(F(12955)*(source_s/N)/(1-source_s/N)) - source_drift["B1"]["analytic_mean_extra_draws"]) < 1e-10
print("PASS: exact conditional law, independent small-field oracle, controls, source receipt checks")
