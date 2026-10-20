"""Plot the published LP2-31 lag-count example. Requires matplotlib.

Run: python scripts/plot_rune_lags.py --output my-lag-chart.svg
Existing output files are never overwritten.
"""
import argparse
from fractions import Fraction
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Output already exists; choose a new filename.')
    data = json.loads((ROOT / 'exports/lp2-31-lag-matches.json').read_text(encoding='utf-8'))
    rows = data['rows']
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':13,
                         'svg.fonttype':'none','svg.hashsalt':'liberpedia-lags-v1'})
    fig, ax = plt.subplots(figsize=(4.8, 5.2))
    ax.bar([r['lag'] for r in rows], [r['matching_pairs']/r['compared_pairs'] for r in rows],
           color='#365e70', width=.75)
    ax.axhline(float(Fraction(data['shuffle_expected_rate_fraction'])),
               color='#8b5b31',linestyle='--',linewidth=1.3)
    ax.set_title('LP2-31 · equal runes at a distance',loc='left',pad=14,fontsize=13)
    ax.set_xlabel('Distance in runes (lag)',fontsize=12)
    ax.set_ylabel('Matching pairs / compared pairs',fontsize=12)
    ax.set_xticks([1,5,10,15,20])
    ax.set_xlim(.3,20.7)
    ax.set_ylim(bottom=0)
    ax.yaxis.set_major_formatter(PercentFormatter(1,decimals=0))
    ax.spines[['top','right']].set_visible(False)
    ax.grid(axis='y',color='#dddddd',linewidth=.6)
    ax.set_axisbelow(True)
    fig.text(.16,.035,'Dashed: count-preserving shuffle expectation.\n269 runes; no wraparound. Not a significance test.',fontsize=9,color='#555555')
    fig.subplots_adjust(left=.16,right=.97,top=.87,bottom=.24)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('xb') as output:
        fig.savefig(output,format='svg',metadata={'Date':None,'Title':'LP2-31 lag coincidence rates, lags 1 through 20',
            'Description':'Archived runes including headings. Each lag d compares 269-d forward pairs. Dashed reference is a shuffle expectation, not a significance threshold.'})
    plt.close(fig)
    print('Wrote',args.output)


if __name__ == '__main__':
    main()
