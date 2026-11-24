import unittest
from matched_schedule import dose, match


class ScheduleContract(unittest.TestCase):
    def test_partial_ends_matched_without_fake_padding(self):
        native = [{'id':'a','tokens':[1,3,9,2]}, {'id':'b','tokens':[7,8,2]}]
        rp = [[1,3,10,2], [1,4,2], [1,9,2], [3,6,2], [1,8,9,2]]
        pairs, shared, _ = match(native, rp)
        self.assertEqual(len(pairs),2)
        self.assertEqual(len(set(shared+[i for _,i in pairs])),4)
        for row, i in pairs:
            self.assertEqual(len(row['tokens']),len(rp[i]))
        self.assertEqual(sum(dose(r['tokens'])['eos'] for r,_ in pairs),2)

    def test_missing_length_does_not_truncate(self):
        rows = [{'id':'a','tokens':[1,2]}, {'id':'b','tokens':[1,6,7,2]}]
        pairs, _, skipped = match(rows, [[1,6,2]]*8)
        self.assertEqual(pairs,[])
        self.assertEqual(skipped,{1:1,3:1})

    def test_budget_is_actual_not_planned(self):
        native = [{'id':str(i),'tokens':[1,6,2]} for i in range(6)]
        pairs, common, _ = match(native, [[1,6,2]]*20,cap=2)
        self.assertEqual(len(pairs),4)
        self.assertEqual(len(common),4)

    def test_invalid_window_rejected(self):
        with self.assertRaises(ValueError):
            match([{'id':'x','tokens':[1]+[7]*257}], [[1,6,2]])


if __name__ == '__main__':
    unittest.main()
