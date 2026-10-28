import json
import unittest
from acquire_jmultiwoz import members, validate_splits


class SelectiveJSONTest(unittest.TestCase):
    def test_escaped_braces_and_nesting(self):
        d = {'train':{'text':'括弧 } ] と quote " と \\', 'nested':[{'x':1}]},
             'test':{'text':'never decode this value'}}
        pairs = list(members(json.dumps(d,ensure_ascii=False).encode()))
        self.assertEqual([k for k,v in pairs], ['train','test'])
        self.assertEqual(json.loads(pairs[0][1]), d['train'])

    def test_unknown_test_value_not_decoded(self):
        # Lexically structured but JSON-invalid value can be skipped by name.
        blob = b'{"test":{"bad": definitely_not_json},"train":{"good":true}}'
        selected = {k:json.loads(v) for k,v in members(blob) if k == 'train'}
        self.assertEqual(selected, {'train':{'good':True}})

    def test_corrupt_truncated_container_fails(self):
        for blob in [b'{"x":{"a":1}', b'{"x":[}', b'{"x":{"a":"unfinished}}']:
            with self.assertRaises(ValueError):
                list(members(blob))

    def test_split_overlap_and_duplicates_rejected(self):
        for split in [dict(train=['x'],dev=['x'],test=[]),
                      dict(train=['x','x'],dev=[],test=[])]:
            with self.assertRaises(AssertionError):
                validate_splits(split)


if __name__ == '__main__':
    unittest.main()
