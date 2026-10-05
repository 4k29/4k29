"""Answer-start emphasis never supervises the prompt or padding."""
import unittest
import torch
from torch.nn import functional as F
from train import answer_prefix_loss

class PrefixLossTests(unittest.TestCase):
    def test_default_is_bitwise_identical_to_original_loss(self):
        torch.manual_seed(429);logits=torch.randn(2,5,12);targets=torch.tensor([[-100,6,7,8,-100],[-100,-100,9,10,2]])
        expected=F.cross_entropy(logits.reshape(-1,12),targets.reshape(-1),label_smoothing=0.01)
        torch.testing.assert_close(answer_prefix_loss(logits,targets,torch.tensor([1,2])),expected,rtol=0,atol=0)
    def test_prefix_gradients_are_emphasized_and_ignored_positions_stay_zero(self):
        logits=torch.zeros(1,5,12,requires_grad=True);targets=torch.tensor([[-100,6,7,8,-100]])
        loss=answer_prefix_loss(logits,targets,torch.tensor([1]),prefix_weight=3,prefix_tokens=2);loss.backward()
        self.assertEqual(logits.grad[0,0].abs().sum().item(),0);self.assertEqual(logits.grad[0,4].abs().sum().item(),0)
        torch.testing.assert_close(logits.grad[0,1,0],3*logits.grad[0,3,0])
        torch.testing.assert_close(logits.grad[0,2,0],3*logits.grad[0,3,0])

if __name__=='__main__':unittest.main()
