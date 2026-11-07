import unittest
from adapter_contract import serialize_linear, serialize_assistant_path, windows

class Contract(unittest.TestCase):
    def posts(self):
        return [dict(id='a',speaker='p',text='甲',replyTo=None),dict(id='b',speaker='p',text='乙',replyTo='a'),dict(id='c',speaker='q',text='丙',replyTo='b')]
    def encode(self,text): return [20+ord(c)%200 for c in text]
    def test_same_person_not_alternated(self):
        stream,marks=serialize_linear(self.posts(),self.encode)
        self.assertEqual([x['speakerRole'] for x in marks],[3,3,4]);self.assertEqual(stream.count(2),3)
    def test_missing_parent_rejected(self):
        p=self.posts();p[1]['replyTo']='unknown'
        with self.assertRaises(ValueError):serialize_linear(p,self.encode)
    def test_branch_rejected(self):
        p=self.posts();p[2]['replyTo']='a'
        with self.assertRaises(ValueError):serialize_linear(p,self.encode)
    def test_third_speaker_rejected(self):
        p=self.posts();p[1]['speaker']='r'
        with self.assertRaises(ValueError):serialize_linear(p,self.encode)
    def test_self_thread_rejected(self):
        p=self.posts();p[2]['speaker']='p'
        with self.assertRaises(ValueError):serialize_linear(p,self.encode)
    def test_no_eos_at_crop(self):
        stream=[1,3]+[27]*600+[2,4,28,2]
        chunks=windows(stream)
        self.assertEqual(chunks[0][-1],27)
        self.assertEqual([t for w in chunks for t in w[1:]],stream[1:])
        self.assertEqual(sum(w[1:].count(2) for w in chunks),2)
    def test_body_special_rejected(self):
        with self.assertRaises(ValueError):serialize_linear(self.posts(),lambda s:[2])
class AssistantContract(unittest.TestCase):
    def path(self):
        return [dict(id=str(i),replyTo=str(i-1)if i else None,writer='w'+str(i),role='prompter'if i%2==0 else'assistant',lang='ja',admitted=True,text='本文')for i in range(4)]
    def test_multiple_human_writers_preserved(self):
        seq,marks=serialize_assistant_path(self.path(),lambda s:[27,28])
        self.assertEqual([m['semanticRole']for m in marks],['prompter','assistant']*2)
        self.assertEqual(len({m['writer']for m in marks}),4);self.assertEqual(seq.count(2),4)
    def test_orphan_not_repaired(self):
        p=self.path();p[1]['replyTo']='missing'
        with self.assertRaises(ValueError):serialize_assistant_path(p,lambda s:[27])
    def test_unadmitted_ancestor_not_removed(self):
        p=self.path();p[0]['admitted']=False
        with self.assertRaises(ValueError):serialize_assistant_path(p,lambda s:[27])
    def test_source_roles_not_inferred(self):
        p=self.path();p[1]['role']='prompter'
        with self.assertRaises(ValueError):serialize_assistant_path(p,lambda s:[27])
if __name__=='__main__':unittest.main()
