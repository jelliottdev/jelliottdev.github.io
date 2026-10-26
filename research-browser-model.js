/* Current records over the supplied research navigation. Grouping is editorial. */
(function(root){
  'use strict';
  const Reader=typeof module==='object'&&module.exports?require('./record-test-view.js'):root.RecordTestView;
  const title=record=>(typeof module==='object'&&module.exports?Reader:root.RecordTestView)?.title(record)||record.title;
  const branchLabels=Object.freeze({"method:combined/operation/8e7b335dd858c0c8":"Use a key and rearrange runes","method:combined/operation/df17f801f70e4ae0":"Select some runes, then decode them","method:combined/operation/7dabd7cf162c9c19":"Three proposed decoding programs","method:feedback":"Using earlier runes as the key","method:repeating-key":"Repeating a key","method:running-key":"Using another text as the key","method:generated-key":"Generating a sequence of keys","method:substitution":"Replacing rune values","method:routes":"Changing the reading order","method:numeric":"Using numbers as keys","method:payload":"Using the number grid","method:steganography":"Looking for hidden content","method:hash-target":"Checking the hidden-page hash","method:combined":"Combining decoding steps","method:blocks":"Decoding groups of runes","method:rune-patterns":"Finding patterns in runes","method:cipher-models":"How the cipher might behave","method:period-alignment":"Repeats and matching positions","method:language":"Comparing possible languages","method:numerical":"Patterns in numbers","method:image-layout":"Measuring page layout","method:transcription":"Checking rune copies","method:payload-analysis":"Examining the number grid","method:decoder-validation":"Checking decoding programs","method:search-calibration":"Checking how searches perform","method:claim-audits":"Checking proposed solutions","method:related-artifacts":"Tracing source material","method:feedback/operation/d5ab54cbb832027d":"Trying different starting keys","method:repeating-key/operation/5e348e7b022cf9bf":"When the key advances or restarts","method:repeating-key/operation/c14d383c39c99825":"Finding a repeating key","method:generated-key/operation/1b1b65d35086732f":"Generating keys from hidden data","method:substitution/operation/02d7a324818c15c0":"Changing rune numbers with a fixed rule","method:rune-patterns/operation/fcc5a70bd2d92f14":"Number patterns inside words","method:cipher-models/operation/3731c9b35952798b":"How easily can a guessed phrase fit?","method:period-alignment/operation/99628b6b114962ea":"Looking for a repeating key length"});
  function build(source,registry){
    if(registry.schema==='liberpedia-experiment-discovery-v1')registry=(typeof module==='object'&&module.exports?require('./research-discovery.js'):root.ResearchDiscovery).normalize(registry);
    const data=structuredClone(source),current=new Map(registry.records.filter(r=>r.status==='published').map(r=>[r.id,r]));
    for(const [id,record] of current){
      const prior=data.records[id]||{};
      data.records[id]={...prior,...record,pages:record.scope.pages,href:'library.html?v=record-panel-20261024#/experiment/'+encodeURIComponent(id)};
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
        if(n.record_id){if(assigned.has(n.record_id))throw Error('Repeated research record: '+n.record_id);assigned.add(n.record_id);n.label=title(current.get(n.record_id));}
        allNodes.push(n);n.children.forEach(child=>add(child,nodeId));
      };
      for(const family of families){add(family,id);children.push(family);members.push(...original.get(family).members.filter(rid=>current.has(rid)));}
      if(id==='aim:other'||id==='aim:unplaced'){
        const ids=id==='aim:other'?data.outside_selected_views:Object.keys(data.records).filter(rid=>!assigned.has(rid)&&!data.outside_selected_views.includes(rid));
        for(const rid of ids){
          if(!current.has(rid)||assigned.has(rid))continue;
          assigned.add(rid);members.push(rid);const nodeId='record:'+rid;children.push(nodeId);
          allNodes.push({id:nodeId,parent:id,label:title(current.get(rid)),color,kind:'record',record_id:rid,children:[],members:[rid],parent_basis:'editorial navigation'});
        }
      }
      allNodes.push({id,parent:'all-research',label,color,kind:'aim',record_id:null,children,members,parent_basis:'editorial navigation'});
    }
    if(assigned.size!==current.size)throw Error('Some published records are missing from the research browser.');
    allNodes.unshift({id:'all-research',parent:null,label:'All research',color:'#263547',kind:'aim',record_id:null,children:routes.map(r=>r[0]),members:[...current.keys()],parent_basis:'editorial navigation'});
    data.views.all={root:'all-research',nodes:allNodes};
    for(const view of Object.values(data.views))for(const n of view.nodes)if(n.record_id&&current.has(n.record_id))n.label=title(current.get(n.record_id));
    for(const view of Object.values(data.views))for(const n of view.nodes)if(!n.record_id&&branchLabels[n.id]){n.technical_label=n.technical_label||n.label;n.label=branchLabels[n.id];}
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
      q:shared.q,type:shared.type,method:shared.method,family:shared.family,sort:q.get('sort')==='top'?'top':shared.sort,...(q.get('saved')==='1'?{saved:'1'}:{}),followups:['1','pending','questions'].includes(q.get('followups'))?q.get('followups'):'',
      p:Math.max(1,Math.min(100000,parseInt(q.get('p')||(oldList?q.get('page'):'1'),10)||1))};
  }
  const api={build,read,branchLabels};if(typeof module!=='undefined')module.exports=api;else root.ResearchBrowserModel=api;
})(globalThis);
