"""Pure serialization reference only; no dataset permission, model or updates implied."""

def serialize_linear(posts, encode):
    """posts: complete, root-first, single parent chain with source-local IDs.

    Do not infer an absent parent, concatenate branches, alternate same-author
    posts into different roles, or map a third participant onto speaker B.
    This conservative reference rejects graphs beyond the existing 2-role contract.
    """
    if len(posts) < 2:
        raise ValueError('Need at least two complete utterances')
    seen, roles, stream, boundaries = set(), {}, [1], []
    for i, post in enumerate(posts):
        ident, speaker, text = post['id'], post['speaker'], post['text']
        if ident in seen or not ident or not speaker or not isinstance(text, str) or not text:
            raise ValueError('Missing identity/text or duplicate node')
        if post.get('replyTo') != (posts[i-1]['id'] if i else None):
            raise ValueError('Missing parent, branch, reordering or incomplete root')
        seen.add(ident)
        if speaker not in roles:
            if len(roles) == 2:
                raise ValueError('More than two human roles is not representable')
            roles[speaker] = 3 + len(roles)
        ids = list(encode(text))
        if not ids or any(not isinstance(t, int) or t < 6 for t in ids):
            raise ValueError('Body must contain only genuine own-BPE body IDs')
        stream += [roles[speaker]] + ids + [2]
        boundaries.append({'post': ident, 'speakerRole': roles[speaker], 'eosOffset': len(stream)-1})
    if len(roles) != 2:
        raise ValueError('A self-thread is not a two-person conversation')
    return stream, boundaries


def windows(stream, context=256):
    """Partition next-token targets once; retained overlap is input-only.

    The first token of later windows is real previous context, never synthetic
    BOS. EOS is copied only from the source turn boundary. Tail PAD is excluded
    by the existing pack() function, not inserted into the real stream.
    """
    if context < 1 or len(stream) < 2:
        raise ValueError('Invalid context or stream')
    return [stream[start:start+context+1] for start in range(0, len(stream)-1, context)]


def serialize_assistant_path(posts, encode):
    """Distinct human-authored assistant-role setting, not two human speakers.

    Input is one complete root-to-leaf path. Actual writer IDs are retained in
    annotations but do not determine model role. Shared ancestors across paths
    must have their repeated dose audited by the dataset builder.
    """
    if len(posts) < 2 or posts[0].get('role') != 'prompter':
        raise ValueError('Need root user and complete response path')
    stream, marks, seen = [1], [], set()
    for i, post in enumerate(posts):
        if not post.get('id') or post['id']in seen:
            raise ValueError('Missing or duplicate message')
        seen.add(post['id'])
        if post.get('replyTo') != (posts[i-1]['id']if i else None):
            raise ValueError('Incomplete ancestry or mixed branches')
        role = post.get('role')
        if role not in ['prompter','assistant'] or role != ('prompter'if i%2==0 else'assistant'):
            raise ValueError('Unknown or nonalternating source semantic role')
        if not post.get('writer') or post.get('lang')!='ja' or post.get('admitted')is not True:
            raise ValueError('Unresolved writer, language or admission')
        ids=list(encode(post['text']))
        if not ids or any(not isinstance(x,int)or x<6 for x in ids):
            raise ValueError('Invalid own-BPE body')
        value=3 if role=='prompter'else 4
        stream += [value]+ids+[2]
        marks.append({'post':post['id'],'semanticRole':role,'writer':post['writer'],'eosOffset':len(stream)-1})
    return stream, marks
