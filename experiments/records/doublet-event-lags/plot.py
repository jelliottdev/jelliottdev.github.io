"""Plot the complete lag-three distribution. Requires matplotlib; checks stay dependency-free."""
import argparse
from collections import Counter
from fractions import Fraction
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
if args.output.exists(): parser.error('Choose a new output filename.')
r=json.loads(Path(__file__).with_name('results.json').read_text())
row=next(x for x in r['lags'] if x['lag']==3)
within=Counter(p['directed'] for p in row['pairs'] if not p['crosses_page'])
cross=Counter(p['directed'] for p in row['pairs'] if p['crosses_page'])
assert [within[i]+cross[i] for i in range(29)]==row['directed_histogram']
expected=[float(Fraction(p))*row['pair_count'] for p in r['shuffle_directed_probabilities']]
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':12,'svg.fonttype':'none','svg.hashsalt':'liberpedia-doublet-events-v1'})
fig,ax=plt.subplots(figsize=(4.8,10.4))
y=list(range(29))
ax.barh(y,[within[i] for i in y],color='#345e70',height=.74,label='Within one page')
ax.barh(y,[cross[i] for i in y],left=[within[i] for i in y],color='#d5dee2',edgecolor='#8a9ba2',linewidth=.5,height=.74,label='Across pages')
ax.scatter(expected,y,marker='|',s=90,color='#8b4e1e',linewidths=1.5,label='Shuffle expectation',zorder=4)
ax.set_yticks(y,[f'+{i}' for i in y]);ax.invert_yaxis()
ax.set_xlabel('Number of comparisons');ax.set_ylabel('Forward difference modulo 29')
ax.xaxis.set_major_locator(MaxNLocator(integer=True));ax.set_xlim(0,11)
ax.spines[['top','right']].set_visible(False);ax.grid(axis='x',color='#eee');ax.set_axisbelow(True)
ax.set_title('Doublet events · lag three',loc='left',fontsize=15,pad=14)
ax.legend(loc='upper left',bbox_to_anchor=(-.23,-.075),frameon=False,fontsize=11)
fig.text(.18,.025,'86 events · 83 comparisons · no end wrap\n75 comparisons cross page boundaries.\nExpected counts are not significance thresholds.',fontsize=10,color='#555555')
fig.subplots_adjust(left=.19,right=.96,top=.93,bottom=.24)
args.output.parent.mkdir(parents=True,exist_ok=True)
fig.savefig(args.output,format=args.output.suffix.lstrip('.'),metadata={'Title':'Lag-three doublet event differences','Description':'All 29 directed differences, split by page boundary. Marks show expected counts after shuffling the fixed event multiset.'})
plt.close(fig)
print('Wrote',args.output)
