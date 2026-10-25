'use strict';
// Reject malformed published source bytes instead of silently changing regex/copy characters.
const fs=require('node:fs'),{execFileSync}=require('node:child_process');
const files=execFileSync('git',['ls-files','-z','--','*.js','*.css','*.html','services/idea-assistant/*.mjs'],{encoding:'utf8',maxBuffer:1024*1024}).split('\0').filter(Boolean).filter(name=>!name.includes('/')||name.startsWith('services/idea-assistant/'));
const failures=[];let count=0;for(const name of files){if(!fs.statSync(name).isFile())continue;count++;try{new TextDecoder('utf-8',{fatal:true}).decode(fs.readFileSync(name));}catch{failures.push(name);}}
if(failures.length){console.error('Published source must be valid UTF-8:\n'+failures.join('\n'));process.exitCode=1;}else console.log('PASS '+count+' published UI and service sources decode as strict UTF-8');
