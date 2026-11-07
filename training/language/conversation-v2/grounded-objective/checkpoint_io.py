"""Lossless experiment snapshots; never silently launch training or overwrite files."""
import argparse, hashlib, io, json, os, pathlib

H = pathlib.Path(__file__).resolve().parent

def verified_bytes(name):
    folder = H / 'run' / name / 'archive'
    manifest = json.loads((folder / 'checkpoint.json').read_text())
    buf = io.BytesIO()
    for c in manifest['chunks']:
        b = (folder / c['path']).read_bytes()
        assert len(b) == c['bytes'] and hashlib.sha256(b).hexdigest() == c['sha256']
        buf.write(b)
    assert buf.tell() == manifest['bytes']
    assert hashlib.sha256(buf.getbuffer()).hexdigest() == manifest['sha256']
    buf.seek(0)
    return buf

def load(name):
    import torch
    raw = H / 'run' / (name + '.pt')
    return torch.load(raw if raw.exists() else verified_bytes(name), map_location='cpu', weights_only=False)

def archive():
    import torch
    import sys
    sys.path.insert(0, str(H.parent))
    from core import digest
    for name in ['full-32', 'response-32', 'full-512', 'response-512', 'full-extra', 'response-extra']:
        raw = H / 'run' / (name + '.pt')
        if not raw.exists():
            verified_bytes(name)
            continue
        state = load(name)
        original_digest = digest(state['trajectory'])
        trace = state['trace']
        (H / 'run' / (name + '-trace.json')).write_text(json.dumps(trace, indent=2) + '\n')
        folder = H / 'run' / name / 'archive'
        folder.mkdir(parents=True, exist_ok=True)
        whole = hashlib.sha256()
        chunks = []
        with raw.open('rb') as f:
            while b := f.read(32 * 1024**2):
                p = folder / ('part-%03d.bin' % len(chunks))
                with p.with_suffix('.pending').open('wb') as out:
                    out.write(b); out.flush(); os.fsync(out.fileno())
                os.replace(p.with_suffix('.pending'), p)
                sha = hashlib.sha256(b).hexdigest()
                assert hashlib.sha256(p.read_bytes()).hexdigest() == sha
                whole.update(b)
                chunks.append(dict(path=p.name, bytes=len(b), sha256=sha))
        extra = name.endswith('extra')
        retained = 608 if extra else int(name.split('-')[-1])
        steps = sorted({int(s['step']) for s in state['trajectory']['optimizer']['state'].values()})
        assert steps == [3470 + retained]
        manifest = dict(sha256=whole.hexdigest(), bytes=raw.stat().st_size, chunks=chunks,
                        inherited_updates=3470, retained_new_updates=retained,
                        active_stage_cursor=state['active_cursor'], optimizer_steps=steps,
                        trajectory_digest=original_digest,
                        contains='complete model/Adam/Torch and private RNG/legacy sampler provenance/active cursor/trace',
                        parent_snapshot=(name.replace('extra', '512') if extra else 'initial3470'),
                        formal_adoption=False)
        (folder / 'checkpoint.json').write_text(json.dumps(manifest, indent=2) + '\n')
        restored = torch.load(verified_bytes(name), map_location='cpu', weights_only=False)
        assert digest(restored['trajectory']) == original_digest
        assert restored['trace'] == trace and restored['active_cursor'] == state['active_cursor']
        raw.unlink()  # Only new redundant working file, after full byte/state verification.
        print(name, 'verified full state and archived', manifest['sha256'], flush=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--archive', action='store_true')
    parser.add_argument('--restore', metavar='NAME')
    parser.add_argument('--output', type=pathlib.Path)
    args = parser.parse_args()
    if args.archive:
        archive()
    elif args.restore and args.output:
        b = verified_bytes(args.restore)
        with args.output.open('xb') as f:
            f.write(b.getbuffer()); f.flush(); os.fsync(f.fileno())
    else:
        parser.error('Use --archive, or --restore NAME --output NEW_FILE')

if __name__ == '__main__':
    main()
