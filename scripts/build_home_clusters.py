"""A source-derived, parent-only overview; no invented links or visual counts."""
from pathlib import Path
import hashlib,json,sys,xml.etree.ElementTree as ET

source=Path(sys.argv[1])/'data/research-map.json'
raw=source.read_bytes();view=json.loads(raw)['views']['solving']
nodes={node['id']:node for node in view['nodes']};root=nodes[view['root']]
families=[nodes[node_id] for node_id in root['children'][:6]]
ET.register_namespace('','http://www.w3.org/2000/svg')
svg=ET.Element('{http://www.w3.org/2000/svg}svg',{'viewBox':'0 0 540 226','fill':'none'})
def el(tag,attrs,parent=svg):
 return ET.SubElement(parent,'{http://www.w3.org/2000/svg}'+tag,{k:str(v) for k,v in attrs.items()})
el('title',{}).text='Selected branches of the LP2 solving map'
el('desc',{}).text='Source parent relationships from '+', '.join(family['label'] for family in families)+'. Open the research map for full labels and records.'
edges=[]
def connect(parent,child,x1,y1,x2,y2,color,width):
 assert nodes[child]['parent']==parent
 el('path',{'d':f'M{x1:.2f} {y1} C{x1:.2f} {(y1+y2)/2} {x2:.2f} {(y1+y2)/2} {x2:.2f} {y2}',
            'stroke':color,'stroke-width':width,'stroke-linecap':'round','data-parent':parent,'data-child':child})
 edges.append((parent,child))
def dot(x,y,r,color,node):
 circle=el('circle',{'cx':f'{x:.2f}','cy':y,'r':r,'fill':color,'data-node':node['id']})
 el('title',{},circle).text=node['label']
leaf_totals=[sum(max(1,min(3,len(nodes[child]['children']))) for child in family['children']) for family in families]
available=492-18*(len(families)-1);total=sum(leaf_totals);cursor=24
for family,count in zip(families,leaf_totals):
 width=available*count/total;center=cursor+width/2;color=family['color']
 connect(root['id'],family['id'],270,15,center,71,color,1.6)
 dot(center,71,3.6,color,family)
 subcursor=cursor
 for child_id in family['children']:
  child=nodes[child_id];grandchildren=[nodes[node_id] for node_id in child['children'][:3]]
  group_width=width*max(1,len(grandchildren))/count;child_x=subcursor+group_width/2
  connect(family['id'],child_id,center,71,child_x,133,color,1.15)
  dot(child_x,133,2.25,color,child)
  for index,grand in enumerate(grandchildren):
   grand_x=subcursor+group_width*(index+.5)/len(grandchildren)
   connect(child_id,grand['id'],child_x,133,grand_x,201,color,.9)
   dot(grand_x,201,1.8,color,grand)
  subcursor+=group_width
 cursor+=width+18
dot(270,15,4.4,root['color'],root)
metadata={'source':'data/research-map.json','sha256':hashlib.sha256(raw).hexdigest(),
 'selection':'First six source families; all immediate children; up to three grandchildren per child.',
 'families':[family['id'] for family in families],'verifiedParentEdges':len(edges),
 'meaning':'A selected preview, not complete coverage or an equivalence claim.'}
el('metadata',{}).text=json.dumps(metadata)
target=Path(sys.argv[1])/'images/home-research-clusters.svg'
ET.ElementTree(svg).write(target,encoding='utf-8')
print(json.dumps({'path':str(target),'bytes':target.stat().st_size,**metadata}))
