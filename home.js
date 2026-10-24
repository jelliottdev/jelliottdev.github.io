'use strict';
(() => {
 const $=id=>document.getElementById(id);
 const idea=$('idea'),form=$('check-idea'),picker=$('file-input'),review=$('file-review');
 const draftKey='liberpedia-home-refined-draft-v1',limit=1500,maxFiles=5,maxBytes=10*1024*1024;
 let files=[],filesTouched=false,saveQueue=Promise.resolve(),saveVersion=0,previewVersion=0;
 const urls=new Map();
 const closeIcon='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m6 6 12 12M18 6 6 18"/></svg>';
 const fileIcon='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M14 3H5v18h14V8zM14 3v5h5M8 12h8M8 16h6"/></svg>';
 const imageTypes=new Set(['image/png','image/jpeg','image/gif','image/webp','image/avif','image/bmp']);
 function status(message=''){const node=$('idea-feedback');node.textContent=message;node.hidden=!message}
 function rememberText(){try{sessionStorage.setItem(draftKey,idea.value)}catch{}}
 function validate(){
  idea.required=files.length===0;
  const over=idea.value.length-limit;
  idea.setCustomValidity(!files.length&&over>0?`${over.toLocaleString()} ${over===1?'character':'characters'} over the text limit. Shorten the idea to continue; attached files are available for local preview only.`:'');
  return files.length>0||over<=0;
 }
 try{idea.value=sessionStorage.getItem(draftKey)||''}catch{}
 validate();
 idea.addEventListener('input',()=>{rememberText();validate();status(!files.length&&idea.value.length>limit?idea.validationMessage:'')});
 const database=new Promise((resolve,reject)=>{
  const request=window.indexedDB.open('liberpedia-home-files-v1',1);
  request.onupgradeneeded=()=>request.result.createObjectStore('drafts',{keyPath:'id'});
  request.onsuccess=()=>resolve(request.result);request.onerror=()=>reject(request.error);
 }).catch(()=>null);
 function transaction(db,mode,operation){return new Promise((resolve,reject)=>{
  const tx=db.transaction('drafts',mode),request=operation(tx.objectStore('drafts'));
  tx.oncomplete=()=>resolve(request.result);tx.onerror=()=>reject(tx.error);tx.onabort=()=>reject(tx.error);
 })}
 function saveFiles(){
  const snapshot=files.slice(),version=++saveVersion;form.dataset.saving='true';
  saveQueue=saveQueue.then(async()=>{
   const db=await database;if(!db)throw Error('Storage unavailable');
   await transaction(db,'readwrite',store=>store.put({id:'home',files:snapshot}));
  }).catch(()=>status('Files are ready to review, but cannot be kept after a reload.')).finally(()=>{
   if(version===saveVersion)form.dataset.saving='false';
  });
 }
 function size(bytes){return bytes<1024?`${bytes} B`:bytes<1024*1024?`${(bytes/1024).toFixed(1)} KB`:`${(bytes/1024/1024).toFixed(1)} MB`}
 function imageUrl(file){if(!urls.has(file.id))urls.set(file.id,URL.createObjectURL(file.blob));return urls.get(file.id)}
 function renderFiles(){
  const target=$('attachments');target.replaceChildren();target.hidden=!files.length;
  files.forEach((file,index)=>{
   const row=document.createElement('div');row.className='attachment';
   const open=document.createElement('button');open.type='button';open.className='attachment-open';open.setAttribute('aria-label',`Preview ${file.name}`);
   if(imageTypes.has(file.type)){const img=document.createElement('img');img.src=imageUrl(file);img.alt='';open.append(img)}else open.innerHTML=fileIcon;
   const info=document.createElement('span');info.className='attachment-info';
   const name=document.createElement('span');name.className='attachment-name';name.textContent=file.name;
   const details=document.createElement('span');details.className='attachment-size';details.textContent=size(file.size);
   info.append(name,details);open.append(info);open.onclick=()=>showReview(index);
   const remove=document.createElement('button');remove.type='button';remove.className='icon-button';remove.setAttribute('aria-label',`Remove ${file.name}`);remove.innerHTML=closeIcon;
   remove.onclick=()=>{filesTouched=true;files.splice(index,1);if(urls.has(file.id)){URL.revokeObjectURL(urls.get(file.id));urls.delete(file.id)}renderFiles();saveFiles();status();$('attach').focus()};
   row.append(open,remove);target.append(row);
  });
  validate();
 }
 function addFiles(selected){
  filesTouched=true;const errors=[];
  for(const file of selected){
   if(files.length>=maxFiles){errors.push('You can attach up to 5 files.');break}
   if(file.size>maxBytes){errors.push(`${file.name} exceeds the 10 MB preview limit.`);continue}
   if(files.some(existing=>existing.name===file.name&&existing.size===file.size&&existing.lastModified===file.lastModified))continue;
   files.push({id:crypto.randomUUID(),name:file.name,size:file.size,type:file.type,lastModified:file.lastModified,blob:file});
  }
  renderFiles();saveFiles();status(errors.join(' '));
 }
 database.then(async db=>{
  if(!db)return;try{const saved=await transaction(db,'readonly',store=>store.get('home'));
   if(!filesTouched&&saved?.files){files=saved.files.filter(file=>file.blob instanceof Blob).slice(0,maxFiles);renderFiles()}
  }catch{}
 });
 $('attach').onclick=()=>picker.click();
 picker.onchange=()=>{addFiles([...picker.files]);picker.value=''};
 window.addEventListener('pagehide',event=>{if(event.persisted)return;for(const url of urls.values())URL.revokeObjectURL(url);urls.clear()});
 let dragDepth=0;
 form.addEventListener('dragenter',event=>{if([...event.dataTransfer.types].includes('Files')){event.preventDefault();dragDepth++;form.classList.add('dragging')}});
 form.addEventListener('dragover',event=>{if([...event.dataTransfer.types].includes('Files')){event.preventDefault();event.dataTransfer.dropEffect='copy'}});
 form.addEventListener('dragleave',()=>{if(--dragDepth<=0){dragDepth=0;form.classList.remove('dragging')}});
 form.addEventListener('drop',event=>{if(event.dataTransfer.files.length){event.preventDefault();addFiles([...event.dataTransfer.files])}dragDepth=0;form.classList.remove('dragging')});
 idea.addEventListener('paste',event=>{const pasted=[...(event.clipboardData?.files||[])];if(pasted.length){if(!event.clipboardData.getData('text/plain'))event.preventDefault();addFiles(pasted)}});
 async function preview(index){
  const version=++previewVersion,file=files[index],target=$('file-preview');target.replaceChildren();
  [...$('review-tabs').children].forEach((button,i)=>button.setAttribute('aria-pressed',String(i===index)));
  if(!file)return;
  if(imageTypes.has(file.type)){const img=document.createElement('img');img.src=imageUrl(file);img.alt=file.name;target.append(img);return}
  if(file.type.startsWith('text/')||/\.(txt|md|py|js|ts|json|csv|log|html|css|yaml|yml|sh|rs|c|cpp)$/i.test(file.name)){
   try{const text=await file.blob.slice(0,200000).text();if(version!==previewVersion)return;
    const pre=document.createElement('pre');pre.textContent=text;target.append(pre);
    if(file.size>200000){const note=document.createElement('p');note.textContent='Showing the first 200 KB. The complete file is kept locally.';target.append(note)}
   }catch{if(version!==previewVersion)return;const note=document.createElement('p');note.textContent='The file could not be previewed. It is still attached.';target.append(note)}
  }else{const note=document.createElement('p');note.textContent=`${file.name} is attached. A preview for this file type isn’t available.`;target.append(note)}
 }
 function showReview(index=0){
  $('review-tabs').replaceChildren();files.forEach((file,i)=>{const button=document.createElement('button');button.type='button';button.textContent=file.name;button.onclick=()=>preview(i);$('review-tabs').append(button)});
  $('review-idea').value=idea.value;$('review-idea').setCustomValidity('');preview(index);if(!review.open)review.showModal();
 }
 $('close-review').onclick=()=>review.close();
 review.addEventListener('close',()=>{idea.value=$('review-idea').value;rememberText();validate()});
 function goToChecker(text){location.assign('investigate.html?q='+encodeURIComponent(text))}
 form.addEventListener('submit',event=>{
  event.preventDefault();rememberText();if(files.length){showReview();return}
  if(!validate()){status(idea.validationMessage);idea.reportValidity();return}
  if(!idea.value.trim()){idea.setCustomValidity('Describe an idea first.');idea.reportValidity();return}
  goToChecker(idea.value);
 });
 $('review-idea').addEventListener('input',()=>{
  $('review-idea').setCustomValidity('');idea.value=$('review-idea').value;rememberText();validate();
 });
 $('review-form').addEventListener('submit',event=>{
  event.preventDefault();const field=$('review-idea'),text=field.value;
  field.setCustomValidity(!text.trim()?'Describe the idea to compare.':text.length>limit?'The current text checker accepts up to 1,500 characters. Keep the original file and describe its idea here.':'');
  if(!field.reportValidity())return;idea.value=text;rememberText();goToChecker(text);
 });
 $('site-search').addEventListener('submit',event=>{
  event.preventDefault();const field=$('search'),query=field.value.trim();
  field.setCustomValidity(query?'':'Enter something to search for.');if(!field.reportValidity())return;
  location.assign('index.html#/search/'+encodeURIComponent(query));
 });
 $('search').addEventListener('input',()=>$('search').setCustomValidity(''));
})();
