"""Added development probes must not hide regression on the original core."""
import contextlib,hashlib,io,json,pathlib,sys,tempfile,unittest
import review
ROOT=pathlib.Path(__file__).resolve().parent
class ReviewTests(unittest.TestCase):
 def test_expanded_pass_does_not_override_original_core_failure(self):
  probes=json.loads((ROOT/'generation-policy.json').read_text())['probes']['validation']
  modern=[p['id'] for p in probes[:9] if p['site']!='aozora'];bad=set(modern[:2])
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);gen=root/'gen.json';manual=root/'manual.json';out=root/'out.json'
   gen.write_text(json.dumps(dict(modelVersion='fixture',partition='validation',rows=[dict(p,validTokens=True) for p in probes])))
   manual.write_text(json.dumps(dict(generationSha256=hashlib.sha256(gen.read_bytes()).hexdigest(),reviewer='Test fixture, never training text',rows=[dict(id=p['id'],grammar=0 if p['id'] in bad else 2,meaning=2,connection=2,repetition=2,breaks=2,fullOutputLoop=False,sentenceClosed=True,reason='Synthetic gate unit test') for p in probes])))
   previous=sys.argv;sys.argv=['review','--generation',str(gen),'--manual',str(manual),'--out',str(out)]
   try:
    with contextlib.redirect_stdout(io.StringIO()):review.main()
   finally:sys.argv=previous
   report=json.loads(out.read_text());self.assertTrue(all(g['gatePassed'] for g in report['groups'].values()));self.assertFalse(report['coreGroups']['contemporary-expository']['gatePassed']);self.assertFalse(report['gatePassed']);self.assertEqual(report['coreTotal'],9)
if __name__=='__main__':unittest.main()
