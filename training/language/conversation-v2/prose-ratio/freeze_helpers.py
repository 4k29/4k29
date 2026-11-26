import runpy
from pathlib import Path

inherited = runpy.run_path(str(Path(__file__).resolve().parents[1]/'prose-development/freeze.py'))
