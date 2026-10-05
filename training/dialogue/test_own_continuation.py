import copy,unittest
import torch
from train import DialogueDecoder
from train_curriculum import load_own_initial_model

class OwnContinuationTests(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(429)
        self.config=dict(vocabulary=16,dim=8,heads=4,hidden=16,layers=1,context=16,dropout=0.12,epsilon=1e-5,semanticTasks=dict(subject=['owner'],attribute=['name']))
        source=DialogueDecoder(self.config)
        self.parent=dict(version='own-test',config=copy.deepcopy(self.config),tokenizer={'bytes':['00']*16},training=dict(randomInitialization=True,externalWeights=False,externalInferenceAPIs=False,teacher=False,sourceSha256='parent',completedSteps=11000,bestStep=9000),tensors={k:dict(shape=list(v.shape),data=v.flatten().tolist()) for k,v in source.state_dict().items()})
        self.old=dict(sourceSha256='parent',tokenizer=copy.deepcopy(self.parent['tokenizer']))
        self.new=dict(tokenizer=copy.deepcopy(self.parent['tokenizer']),provenance=dict(parentCorpusSha256='parent'))
    def test_generating_weights_and_matching_label_rows_are_preserved(self):
        config=copy.deepcopy(self.config);config['semanticTasks']['subject']=['apple','owner']
        model=DialogueDecoder(config);new_row=model.semantic['subject'].weight[0].detach().clone()
        lineage=load_own_initial_model(model,self.parent,self.old,self.new)
        for key,value in model.state_dict().items():
            if not key.startswith('semantic.'):self.assertTrue(torch.equal(value,torch.tensor(self.parent['tensors'][key]['data']).reshape(value.shape)),key)
        old=self.parent['tensors']['semantic.subject.weight']
        self.assertTrue(torch.equal(model.semantic['subject'].weight[1],torch.tensor(old['data']).reshape(old['shape'])[0]))
        self.assertTrue(torch.equal(model.semantic['subject'].weight[0],new_row))
        self.assertEqual(lineage['newSemanticLabels']['subject'],['apple'])
        self.assertEqual(lineage['selectedParentStep'],9000)
        self.assertEqual(lineage['completedParentUpdates'],11000)
        self.assertFalse(lineage['optimizerReused'])
    def test_refuses_outside_teacher_or_missing_own_lineage(self):
        for field,value in [('externalWeights',True),('externalInferenceAPIs',True),('teacher',True),('randomInitialization',False)]:
            parent=copy.deepcopy(self.parent);parent['training'][field]=value
            with self.assertRaises(ValueError):load_own_initial_model(DialogueDecoder(self.config),parent,self.old,self.new)
    def test_refuses_changed_vocabulary_source_or_architecture(self):
        cases=[]
        new=copy.deepcopy(self.new);new['tokenizer']['bytes'][0]='ff';cases.append((self.parent,self.old,new,self.config))
        old=copy.deepcopy(self.old);old['sourceSha256']='other';cases.append((self.parent,old,self.new,self.config))
        new=copy.deepcopy(self.new);new['provenance']['parentCorpusSha256']='other';cases.append((self.parent,self.old,new,self.config))
        config=copy.deepcopy(self.config);config['context']=32;cases.append((self.parent,self.old,self.new,config))
        for parent,old,new,config in cases:
            with self.assertRaises(ValueError):load_own_initial_model(DialogueDecoder(config),parent,old,new)
    def test_declared_position_extension_preserves_parent_rows_and_seeds_new_rows(self):
        config=copy.deepcopy(self.config);config['context']=32
        new=copy.deepcopy(self.new);new['provenance']['architectureChange']={'extendedPositionEmbeddings':{'parent':16,'current':32}}
        model=DialogueDecoder(config);seeded=model.position.weight[16:].detach().clone()
        lineage=load_own_initial_model(model,self.parent,self.old,new)
        old=self.parent['tensors']['position.weight']
        self.assertTrue(torch.equal(model.position.weight[:16],torch.tensor(old['data']).reshape(old['shape'])))
        self.assertTrue(torch.equal(model.position.weight[16:],seeded))
        self.assertEqual(lineage['extendedPositionEmbeddings'],{'parent':16,'current':32})
    def test_refuses_missing_shape_mismatch_and_nonfinite_generating_weights(self):
        for mode in ['missing','shape','nonfinite']:
            parent=copy.deepcopy(self.parent)
            if mode=='missing':del parent['tensors']['token.weight']
            elif mode=='shape':parent['tensors']['token.weight']['shape']=[8,16]
            else:parent['tensors']['token.weight']['data'][0]=float('nan')
            with self.assertRaises(ValueError):load_own_initial_model(DialogueDecoder(self.config),parent,self.old,self.new)

if __name__=='__main__':unittest.main()
