"""Exercise low-disk archival through a real isolated Git index/object store."""
import contextlib,hashlib,io,json,pathlib,subprocess,tempfile,unittest
import archive_checkpoint as archive

class ArchiveTests(unittest.TestCase):
    def test_git_retains_all_checkpoint_bytes_after_workspace_copy_removed(self):
        with tempfile.TemporaryDirectory(dir='/dev/shm') as temporary:
            repo=pathlib.Path(temporary)/'repo';repo.mkdir()
            subprocess.run(['git','init','-q',str(repo)],check=True)
            (repo/'.git/info/sparse-checkout').write_text('/*\n')
            archive.REPO=repo;archive.HERE=repo/'training/language/conversation-v2/epoch1'
            archive.HERE.mkdir(parents=True)
            source=pathlib.Path(temporary)/'source';source.mkdir()
            blobs=[b'own-checkpoint-first-part\0',bytes(range(256))]
            rows=[]
            for i,b in enumerate(blobs):
                p=source/f'part-{i}.bin';p.write_bytes(b)
                rows.append(dict(path=p.name,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
            record=dict(filename='checkpoint.pt',bytes=sum(map(len,blobs)),sha256=hashlib.sha256(b''.join(blobs)).hexdigest(),chunks=rows)
            manifest=source/'checkpoint.pt.chunks.json';manifest.write_text(json.dumps(record))
            with contextlib.redirect_stdout(io.StringIO()):archive.archive(manifest,'medium')
            for row,b in zip(rows,blobs):
                p=archive.HERE/'medium/archive'/row['path']
                self.assertFalse(p.exists())
                actual=subprocess.check_output(['git','show',':'+str(p.relative_to(repo))],cwd=repo)
                self.assertEqual(actual,b)
            self.assertEqual(json.loads((archive.HERE/'medium/archive/git-archive-receipt.json').read_text())['sha256'],record['sha256'])
            self.assertEqual(b''.join((source/r['path']).read_bytes()for r in rows),b''.join(blobs))

if __name__=='__main__':unittest.main()
