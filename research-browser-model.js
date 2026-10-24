/* Current records over the supplied research navigation. Grouping is editorial. */
(function(root){
  'use strict';
  function build(source,registry){
    const data=structuredClone(source),current=new Map(registry.records.filter(r=>r.status==='published').map(r=>[r.id,r]));
    for(const [id,record] of current){
      const prior=data.records[id]||{};
      data.records[id]={...prior,...record,pages:record.scope.pages,href:'library.html#/experiment/'+encodeURIComponent(id)};
    }
    for(const id of Object.keys(data.records))if(!current.has(id))delete data.records[id];
    const original=new Map(Object.values(data.views).flatMap(view=>view.nodes).map(n=>[n.id,n]));
    const routes=[
      ['solve-lp2','Solve LP2','#2563eb',original.get(data.views.solving.root).children],
      ['aim:understand','Understand the manuscript','#0d9488',['method:rune-patterns','method:cipher-models','method:period-alignment','method:language','method:numerical','method:image-layout','method:payload-analysis']],
      ['aim:validate','Check methods & tools','#7c3aed',['method:decoder-validation','method:search-calibration','method:claim-audits']],
      ['aim:sources','Verify sources','#0369a1',['method:transcription','method:related-artifacts']],
      ['aim:other','Other Cicada material','#be185d',[]],
      ['aim:unplaced','Other records','#64748b',[]]
    ];
    const allNodes=[],assigned=new Set();
    for(const [id,label,color,families] of routes){
      const children=[],members=[];
      const add=(nodeId,parent)=>{
        const prior=original.get(nodeId);if(!prior)throw Error('Missing research branch: '+nodeId);
        const n=structuredClone(prior);n.parent=parent;n.parent_basis=families.includes(nodeId)?'editorial navigation':'source';
        n.members=n.members.filter(rid=>current.has(rid));
        if(n.record_id){if(assigned.has(n.record_id))throw Error('Repeated research record: '+n.record_id);assigned.add(n.record_id);n.label=current.get(n.record_id).title;}
        allNodes.push(n);n.children.forEach(child=>add(child,nodeId));
      };
      for(const family of families){add(family,id);children.push(family);members.push(...original.get(family).members.filter(rid=>current.has(rid)));}
      if(id==='aim:other'||id==='aim:unplaced'){
        const ids=id==='aim:other'?data.outside_selected_views:Object.keys(data.records).filter(rid=>!assigned.has(rid)&&!data.outside_selected_views.includes(rid));
        for(const rid of ids){
          if(!current.has(rid)||assigned.has(rid))continue;
          assigned.add(rid);members.push(rid);const nodeId='record:'+rid;children.push(nodeId);
          allNodes.push({id:nodeId,parent:id,label:current.get(rid).title,color,kind:'record',record_id:rid,children:[],members:[rid],parent_basis:'editorial navigation'});
        }
      }
      allNodes.push({id,parent:'all-research',label,color,kind:'aim',record_id:null,children,members,parent_basis:'editorial navigation'});
    }
    if(assigned.size!==current.size)throw Error('Some published records are missing from the research browser.');
    allNodes.unshift({id:'all-research',parent:null,label:'All research',color:'#263547',kind:'aim',record_id:null,children:routes.map(r=>r[0]),members:[...current.keys()],parent_basis:'editorial navigation'});
    data.views.all={root:'all-research',nodes:allNodes};
    for(const view of Object.values(data.views))for(const n of view.nodes)if(n.record_id&&current.has(n.record_id))n.label=current.get(n.record_id).title;
    return data;
  }
  function read(hash,preferredMode='graph',selector){
    const legacy=/^#\/(research|research-map)(?:\?|$)/.test(hash),oldList=/^#\/research(?:\?|$)/.test(hash);
    const q=new URLSearchParams(legacy?hash.split('?')[1]||'':hash.replace(/^#/,''));
    const shared=selector(q);
    const result=q.get('result');
    return {view:['solving','analytics'].includes(q.get('view'))?q.get('view'):'all',branch:q.get('branch')||'',record:/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(q.get('record')||'')?q.get('record'):'',
      page:/^lp[12]-\d{2}$/.test(q.get('page')||'')?q.get('page'):'',colour:q.get('colour')==='results'?'results':'methods',
      result:['supported','not-supported','inconclusive'].includes(result)?result:shared.outcome,mode:['graph','list'].includes(q.get('mode'))?q.get('mode'):oldList?'list':preferredMode,
      q:shared.q,type:shared.type,method:shared.method,family:shared.family,sort:shared.sort,
      p:Math.max(1,Math.min(100000,parseInt(q.get('p')||(oldList?q.get('page'):'1'),10)||1))};
  }
  const api={build,read};if(typeof module!=='undefined')module.exports=api;else root.ResearchBrowserModel=api;
})(globalThis);
