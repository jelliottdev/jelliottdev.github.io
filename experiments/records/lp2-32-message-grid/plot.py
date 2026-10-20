"""Draw the tested layout and central perimeter. Optional Matplotlib dependency."""
import argparse
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
if args.output.exists():parser.error('Choose a new output filename.')
r=json.loads(Path(__file__).with_name('results.json').read_text())
values={(c['row'],c['column']):c['prime'] for c in r['cells']}
ring={(c['row'],c['column']) for c in r['central_perimeter']}
assert len(ring)==16 and sum(values[k] for k in ring)==1136
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':12,'svg.fonttype':'none','svg.hashsalt':'liberpedia-grid32-v1'})
fig,(ax,bx)=plt.subplots(2,1,figsize=(4.8,9.6))
for row in range(1,12):
    for col in range(1,12):
        color='#dbe6ec' if row==1 or col==1 else '#f5f5f1'
        if (row,col) in ring:color='#345e70'
        ax.add_patch(Rectangle((col-.5,row-.5),1,1,facecolor=color,edgecolor='white',linewidth=1))
ax.set(xlim=(.5,11.5),ylim=(11.5,.5),xticks=range(1,12),yticks=range(1,12))
ax.set_title('LP2-32 · the tested layout',loc='left',fontsize=14,pad=14)
ax.set_xlabel('Column');ax.set_ylabel('Row');ax.set_aspect('equal')
ax.tick_params(labelsize=10)
for spine in ax.spines.values():spine.set_visible(False)
ax.text(0,-.24,'Pale blue: first row = 563; first column = 569.\nDark blue: the central 5 × 5 perimeter.',transform=ax.transAxes,fontsize=10,va='top')
for row in range(4,9):
    for col in range(4,9):
        selected=(row,col) in ring
        bx.add_patch(Rectangle((col-.5,row-.5),1,1,facecolor='#345e70' if selected else '#f5f5f1',edgecolor='white',linewidth=1.5))
        bx.text(col,row,str(values[row,col]),ha='center',va='center',color='white' if selected else '#686868',fontsize=14)
bx.set(xlim=(3.5,8.5),ylim=(8.5,3.5),xticks=range(4,9),yticks=range(4,9))
bx.set_title('Central block · prime values',loc='left',fontsize=14,pad=14)
bx.set_xlabel('Column');bx.set_ylabel('Row');bx.set_aspect('equal')
for spine in bx.spines.values():spine.set_visible(False)
fig.text(.16,.025,'Add the 16 dark cells once: 1,136.\nThe nine pale interior cells are excluded.\nRow-major rearrangement, not printed line breaks.',fontsize=10,color='#444444')
fig.subplots_adjust(left=.16,right=.95,top=.94,bottom=.13,hspace=.63)
metadata={'Title':'LP2-32 grid and central perimeter','Description':'Row-major 11 by 11 layout. First row and column highlighted; detailed 5 by 5 inset with 16 selected border prime values.'}
if args.output.suffix.lower()=='.svg':metadata['Date']=None
fig.savefig(args.output,format=args.output.suffix.lstrip('.'),metadata=metadata)
plt.close(fig)
print('Wrote',args.output)
