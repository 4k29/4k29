import unittest
import torch
from response_position_ce import Turn, build_weights, position_weighted_main_ce


class ResponseCeTests(unittest.TestCase):
    def setUp(self):
        self.rows = [dict(site="human-chat", unit="u", start=0, length=10, prefixLength=1, cleanCharacterStart=True)]
        # Original tokens: BOS, turn0 three tokens, turn1 three, turn2 two.
        self.turns = {"u": [Turn(0,1,4), Turn(1,4,7), Turn(2,7,9)]}
        self.y = torch.tensor([[6,7,16,8,9,16,10,16,2]])
        self.end = self.y.eq(16)

    def test_selected_reply_preserves_mass_and_end_exclusion(self):
        w,a = build_weights(self.rows,self.y,self.end,self.turns)
        self.assertIn(a[0]["selectedTurn"],[1,2])
        self.assertEqual(w.sum().item(),6)
        self.assertEqual(w[0,8].item(),1)
        self.assertEqual(w[0,:8].sum().item(),5)
        self.assertTrue(bool(w[self.end].eq(0).all()))

    def test_original_denominator_and_gradient_localization(self):
        w,_ = build_weights(self.rows,self.y,self.end,self.turns)
        logits = torch.zeros((1,9,20),requires_grad=True)
        value=position_weighted_main_ce(logits,self.y,self.end,w)
        self.assertAlmostEqual(value.item(),torch.log(torch.tensor(20.)).item()*6/9,places=6)
        value.backward()
        chosen=w.ne(0)
        self.assertGreater(logits.grad[chosen].abs().sum().item(),0)
        self.assertLess(logits.grad[~chosen].abs().sum().item(),1e-6)
        self.assertGreater(logits.grad[0,8].abs().sum().item(),0)

    def test_missing_true_alignment_does_not_merge_turns(self):
        turns={"u":[Turn(0,1,4),Turn(1,4,None),Turn(2,None,9)]}
        w,a=build_weights(self.rows,self.y,self.end,turns)
        self.assertIsNone(a[0]["selectedTurn"])
        torch.testing.assert_close(w,(~self.end).double())

    def test_cropped_reply_falls_back_to_previous_complete(self):
        rows=[dict(self.rows[0],length=8)]
        w,a=build_weights(rows,self.y[:,:7],self.end[:,:7],self.turns)
        self.assertEqual(a[0]["selectedTurn"],1)
        self.assertEqual(w.sum().item(),5)

    def test_cropped_context_not_claimed_complete(self):
        rows=[dict(self.rows[0],start=5,length=5,prefixLength=1)]
        y=self.y[:,5:9];end=self.end[:,5:9]
        w,a=build_weights(rows,y,end,self.turns)
        self.assertIsNone(a[0]["selectedTurn"])
        torch.testing.assert_close(w,(~end).double())

    def test_reply_overlapping_original_prefix_is_ineligible(self):
        rows=[dict(self.rows[0],prefixLength=8)]
        y=self.y.clone();y[:,:7]=-100;end=y.eq(16)
        w,a=build_weights(rows,y,end,self.turns)
        self.assertIsNone(a[0]["selectedTurn"])
        torch.testing.assert_close(w,(y.ne(-100)&~end).double())

    def test_nonhuman_and_unclean_start_exact_fallback(self):
        for row in [dict(self.rows[0],site="aozora"),dict(self.rows[0],cleanCharacterStart=False)]:
            w,a=build_weights([row],self.y,self.end,self.turns)
            torch.testing.assert_close(w,(~self.end).double())
            self.assertIsNone(a[0]["selectedTurn"])

    def test_fallback_loss_exact_old_reduction(self):
        logits=torch.randn((1,9,20))
        row=dict(self.rows[0],site="aozora")
        w,_=build_weights([row],self.y,self.end,self.turns)
        old=torch.nn.functional.cross_entropy(logits.reshape(-1,20),self.y.reshape(-1))
        old=old-torch.nn.functional.cross_entropy(logits[self.end],self.y[self.end],reduction="sum")/self.y.ne(-100).sum()
        self.assertTrue(torch.equal(position_weighted_main_ce(logits,self.y,self.end,w),old))

    def test_determinism_and_no_rng_consumption(self):
        before=torch.get_rng_state().clone()
        w,a=build_weights(self.rows,self.y,self.end,self.turns)
        w2,a2=build_weights(self.rows,self.y,self.end,self.turns)
        self.assertEqual(a,a2);torch.testing.assert_close(w,w2)
        self.assertTrue(torch.equal(before,torch.get_rng_state()))

    def test_mass_violation_and_newline_restoration_rejected(self):
        logits=torch.zeros((1,9,20))
        w,_=build_weights(self.rows,self.y,self.end,self.turns)
        with self.assertRaises(ValueError):position_weighted_main_ce(logits,self.y,self.end,w*2)
        w[0,2]=1
        with self.assertRaises(ValueError):position_weighted_main_ce(logits,self.y,self.end,w)

    def test_bos_and_eos_original_weights_protected(self):
        y=self.y.clone();y[0,0]=1
        w,_=build_weights(self.rows,y,self.end,self.turns)
        self.assertEqual(w[0,0].item(),1)
        self.assertEqual(w[0,8].item(),1)
        self.assertEqual(w.sum().item(),6)
        w[0,8]=0;w[0,0]=2
        with self.assertRaises(ValueError):
            position_weighted_main_ce(torch.zeros((1,9,20)),y,self.end,w)

    def test_skipped_authentic_turn_ordinal_rejected(self):
        with self.assertRaises(ValueError):
            build_weights(self.rows,self.y,self.end,{"u":[Turn(0,1,4),Turn(2,4,9)]})

    def test_zero_active_reply_keeps_old_objective(self):
        turns={"u":[Turn(0,1,7),Turn(1,7,8)]}
        y=self.y.clone();y[0,6]=16;end=y.eq(16)
        w,a=build_weights(self.rows,y,end,turns)
        self.assertIsNone(a[0]["selectedTurn"])
        torch.testing.assert_close(w,(~end).double())


if __name__=="__main__":unittest.main()
