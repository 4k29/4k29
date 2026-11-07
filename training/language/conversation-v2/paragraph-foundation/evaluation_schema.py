"""Keep original source and unmodified generated payload in separate fields."""
def combine_case(source,generation):
 result=dict(source)
 if 'text'in result:result['source_reference_text']=result.pop('text')
 overlap=set(result)&set(generation)
 if overlap:raise ValueError('Unexpected source/generation field collision: '+','.join(sorted(overlap)))
 result.update(generation);return result
