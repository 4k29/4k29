"""Standalone research figure; neither scoring nor checkpoint selection."""
import hashlib
import json
import pathlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

D = pathlib.Path(__file__).resolve().parent


def main():
    results = json.loads((D/'RESULTS.json').read_text())
    models = {r['model']: r for r in results['results']}
    steps = [0, 1997, 3994, 6361]
    targets = [0, 2000891, 4000227, 6372025]
    x = [t/1e6 for t in targets]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), constrained_layout=True)
    for key, label, color in [('old_prose', 'Existing prose DEV', '#315b86'),
                              ('caption_DEV', 'Caption DEV', '#b36828')]:
        axes[0].plot(x, [models[f'B-{s}']['summary']['NLL'][key]['nll'] for s in steps],
                     marker='o', label=label, color=color)
    axes[0].set(title='B lineage: same-source teacher-forced NLL',
                xlabel='Additional retained targets (millions)', ylabel='Nats per token', ylim=(0, 6))
    axes[0].legend(frameon=False)
    reviewed = [models[f'B-{s}']['main_assistant_reading'] for s in steps[1:]]
    axes[1].plot(x[1:], [r['caption_short_text_counts']['clear']/32*100 for r in reviewed],
                 marker='o', label='Prefix + short caption continuation (n=32)', color='#b36828')
    axes[1].plot(x[1:], [sum(r['developed_coherent_prose'].values())/45*100 for r in reviewed],
                 marker='s', label='Developed coherent prose (n=45)', color='#315b86')
    axes[1].set(title='Different tasks; no dialogue success established',
                xlabel='Additional retained targets (millions)', ylabel='Exploratory reading: clear cases (%)',
                ylim=(-3, 100))
    axes[1].legend(frameon=False, loc='upper left', fontsize=8)
    for axis in axes:
        axis.grid(alpha=.2)
        axis.spines[['top', 'right']].set_visible(False)
    fig.suptitle('Corpus adaptation is not proof of general Japanese ability', fontsize=13)
    fig.supxlabel('Exposed DEV; one unblinded assistant; caption cases include ending-only completions. No independent human evaluation.', fontsize=8)
    fig.savefig(D/'learning-summary.png', dpi=160)
    fig.savefig(D/'learning-summary.svg', metadata={'Date': None})
    plt.close(fig)
    (D/'FIGURE_SOURCES.json').write_text(json.dumps(dict(
        results_sha256=hashlib.sha256((D/'RESULTS.json').read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
        scope='Descriptive figure; caption short completion and developed prose have different denominators/tasks.'), indent=2)+'\n')


if __name__ == '__main__':
    main()
