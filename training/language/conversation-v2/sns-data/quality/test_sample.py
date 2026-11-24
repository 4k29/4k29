import unittest
from sample import select
class SampleTest(unittest.TestCase):
    def rec(self,id,split='TRAIN',family=None,text='日本語'):
        return dict(id=id,split=split,conversation_family=family or id,source='x',utterances=[dict(text=text),dict(text='はい')])
    def test_order_invariant_and_family_limit(self):
        a=[self.rec(str(i),family=str(i//2)) for i in range(100)]
        x=select(a);self.assertEqual(x,select(a[::-1]));self.assertEqual(x['selectedThreads'],40)
        self.assertEqual(len({r['record']['conversation_family'] for r in x['threads']}),40)
    def test_dev_and_long_excluded_no_truncation(self):
        a=[self.rec('a',split='DEV'),self.rec('b',text='あ'*12001),self.rec('c')]
        x=select(a);self.assertEqual(x['selectedThreads'],1);self.assertEqual(x['threads'][0]['record'],a[2])
    def test_unassigned_explicit(self):
        self.assertEqual(select([self.rec('a','unassigned')])['selectedThreads'],1)
        self.assertEqual(select([self.rec('a',None)])['selectedThreads'],0)
if __name__=='__main__':unittest.main()
