"""Small invariant tests only. No checkpoint reads, restores or optimizer updates."""
import unittest

import torch

from response_position_ce import Turn, build_weights, position_weighted_main_ce
from validation_common import exact


class PreflightContracts(unittest.TestCase):
    def fixture(self):
        rows = [dict(site='human-chat', unit='u', start=0, length=10,
                     prefixLength=1, cleanCharacterStart=True)]
        turns = {'u': [Turn(0,1,4), Turn(1,4,7), Turn(2,7,9)]}
        targets = torch.tensor([[6,7,16,8,9,16,10,16,2]])
        end = targets.eq(16)
        weights, audits = build_weights(rows, targets, end, turns)
        return rows, turns, targets, end, weights, audits

    def test_direct_loss_rejects_invalid_end_masks(self):
        _, _, y, end, weights, _ = self.fixture()
        logits = torch.zeros((1,9,20))
        for invalid in (end.long(), end[:,:-1]):
            with self.assertRaises(ValueError):
                position_weighted_main_ce(logits, y, invalid, weights)
        invalid = end.clone(); invalid[0,0] = True
        with self.assertRaises(ValueError):
            position_weighted_main_ce(logits, y, invalid, weights)
        masked = y.clone(); masked[0,2] = -100
        with self.assertRaises(ValueError):
            position_weighted_main_ce(logits, masked, end, weights)

    def test_independent_logit_gradient_reference(self):
        _, _, y, end, weights, _ = self.fixture()
        logits = torch.linspace(-1,1,180).reshape(1,9,20).requires_grad_()
        other = logits.detach().clone().requires_grad_()
        actual = position_weighted_main_ce(logits, y, end, weights)
        ce = torch.nn.functional.cross_entropy(other.reshape(-1,20), y.reshape(-1), reduction='none').reshape_as(y)
        reference = (ce * weights.float()).sum() / y.ne(-100).sum()
        self.assertTrue(torch.allclose(actual.detach(), reference.detach(), atol=1e-7, rtol=1e-6))
        actual.backward(); reference.backward()
        self.assertTrue(torch.allclose(logits.grad, other.grad, atol=1e-7, rtol=1e-6))

    def test_fallback_parameter_gradients_bitwise(self):
        rows, turns, y, end, _, _ = self.fixture()
        rows[0]['site'] = 'nonhuman'
        weights, _ = build_weights(rows, y, end, turns)
        # Multiple parameter tensors, not merely an independent logit variable.
        a = torch.nn.Linear(3,20); b = torch.nn.Linear(3,20)
        b.load_state_dict(a.state_dict())
        inputs = torch.linspace(-1,1,27).reshape(1,9,3)
        logits = a(inputs)
        baseline = torch.nn.functional.cross_entropy(logits.reshape(-1,20), y.reshape(-1))
        baseline -= torch.nn.functional.cross_entropy(logits[end], y[end], reduction='sum')/y.ne(-100).sum()
        treatment = position_weighted_main_ce(b(inputs), y, end, weights)
        baseline.backward(); treatment.backward()
        self.assertTrue(torch.equal(baseline, treatment))
        self.assertTrue(all(torch.equal(p.grad,q.grad) for p,q in zip(a.parameters(),b.parameters())))

    def test_streaming_variance_is_full_vector_population_variance(self):
        from gradient_audit import Moments
        samples = [torch.tensor([1.,0.]), torch.tensor([0.,1.]), torch.tensor([-1.,0.])]
        m = Moments()
        for sample in samples: m.add(sample)
        stack = torch.stack(samples).double()
        expected = float(((stack-stack.mean(0))**2).sum(1).mean())
        self.assertAlmostEqual(m.result()['populationVectorGradientVariance'], expected, places=12)
        self.assertAlmostEqual(m.result()['populationGradientNormVariance'], 0., places=12)
        self.assertGreater(expected, 0.)

    def test_exact_checks_dtype_and_counter(self):
        self.assertFalse(exact(torch.tensor([1.]), torch.tensor([1.], dtype=torch.float64)))
        self.assertFalse(exact({'completedValidationUpdates':2}, {'completedValidationUpdates':10}))


if __name__ == '__main__':
    unittest.main()
