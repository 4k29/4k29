import pathlib,select,profile,cProfile,subprocess
p=pathlib.Path(__file__).resolve().parent
for m in [select,profile,cProfile,subprocess]:
 assert pathlib.Path(m.__file__).resolve().parent!=p,m.__name__
print('Standard-library import isolation passed; optimizer0,forward0')
