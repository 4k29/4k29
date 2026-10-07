"""Added easy probes and short closure must not mask inherited failures."""
import unittest
from review import review
class Gates(unittest.TestCase):
 def test_all_scopes_and_full_meaning_required(self):
  output=dict(partition='validation',modelVersion='fixture',rows=[]);manual=dict(rows=[])
  for i in range(17):
   output['rows'].append(dict(id=str(i),site='aozora' if i<3 else 'mic',validTokens=True))
   manual['rows'].append(dict(id=str(i),grammar=2,meaning=2,connection=2,repetition=2,breaks=2,sentenceClosed=True,fullOutputLoop=False,fullOutputMeaningful=True,reason='Fixture'))
  policy=dict(acceptance=dict(minimumTotalScore=9,minimumGrammarScore=2,minimumConnectionScore=2,minimumSentenceSuccessRate=.8,minimumFullOutputNonLoopRate=.9));meaning=dict(minimumMeaningfulFullOutputRate=.8)
  parent=dict(probes=dict(validation=[dict(id=str(i)) for i in range(13)]));original=dict(probes=dict(validation=[dict(id=str(i)) for i in range(9)]))
  self.assertTrue(review(output,manual,policy,meaning,parent,original)['gatePassed'])
  # Original modern subset fails at4/6; enlarged modern subset still passes12/14.
  for i in [3,4]:manual['rows'][i]['fullOutputMeaningful']=False
  result=review(output,manual,policy,meaning,parent,original);self.assertTrue(result['scopes']['expanded17']['gatePassed']);self.assertFalse(result['scopes']['original9']['gatePassed']);self.assertFalse(result['gatePassed'])
  for j in manual['rows']:j['fullOutputMeaningful']=False
  result=review(output,manual,policy,meaning,parent,original);self.assertEqual(result['passed'],17);self.assertEqual(result['fullOutputNonLoop'],17);self.assertFalse(result['naturalLanguageEstablished'])
if __name__=='__main__':unittest.main()
