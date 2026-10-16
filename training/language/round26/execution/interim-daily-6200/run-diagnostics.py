import subprocess,json
commands=[['python', 'training/language/round26/execution/evaluate_daily.py', '--model', '/workspace/4k29/training/language/round26/execution/interim-daily-6200/model.js', '--out', '/workspace/4k29/training/language/round26/execution/interim-daily-6200/daily-python.json'], ['python', 'training/language/round26/execution/daily_human_likelihood.py', '--model', '/workspace/4k29/training/language/round26/execution/interim-daily-6200/model.js', '--out', '/workspace/4k29/training/language/round26/execution/interim-daily-6200/human-development-likelihood.json']]
for cmd in commands:
 subprocess.run(cmd,check=True)
