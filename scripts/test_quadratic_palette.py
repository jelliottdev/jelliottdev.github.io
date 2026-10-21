"""Independent small-domain controls for the quadratic coefficient solver."""
import itertools
import unittest

from run_quadratic_palette import coefficients, divisors
from check_quadratic_palette import lifted_coefficients, factored_divisors


class QuadraticControls(unittest.TestCase):
    def test_solver_against_all_coefficients(self):
        # Includes moduli where 6 is not invertible. Compare all anchor images,
        # including repeated images, rather than only the intended prime palette.
        for m in range(2, 19):
            direct = {}
            for a,b,c in itertools.product(range(m), repeat=3):
                images = tuple((a*x*x+b*x+c) % m for x in (2,3,5))
                direct.setdefault(images, set()).add((a,b,c))
            for images in itertools.product(range(m), repeat=3):
                self.assertEqual(set(coefficients(*images,m)), direct.get(images,set()), (m,images))
                self.assertEqual(set(lifted_coefficients(*images,m)), direct.get(images,set()), (m,images))

    def test_divisors_against_linear_scan(self):
        for n in range(1,1000):
            self.assertEqual(divisors(n), {d for d in range(1,n+1) if n % d == 0})
            self.assertEqual(set(factored_divisors(n)), {d for d in range(1,n+1) if n % d == 0})

    def test_scope_counterexamples(self):
        self.assertEqual([(22*x*x+16*x+10) % 127 for x in (2,3,5)], [3,2,5])
        self.assertEqual((22*7*7+16*7+10) % 127, 57)
        # A nonzero quadratic coefficient need not mean a nonidentity function.
        self.assertEqual([(55*x*x+56*x) % 110 for x in range(110)], list(range(110)))


if __name__ == '__main__':
    unittest.main()
