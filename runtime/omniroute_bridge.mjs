// Local management uses the shipped OmniRoute API client and its machine credential.
// stdout is captured privately by Python; never run this bridge with terminal output.
import { writeFile } from 'node:fs/promises';
import { pathToFileURL } from 'node:url';
import { join } from 'node:path';
const sameList=(a,b)=>JSON.stringify([...a].sort())===JSON.stringify([...b].sort());
// Only permission metadata is kept; GET returns a partially masked secret that must never reach a backup.
const keyState=k=>({id:k.id,name:k.name,modelAccessMode:k.modelAccessMode,allowedModels:Array.isArray(k.allowedModels)?[...k.allowedModels]:[]});
try {
  let input=''; for await(const chunk of process.stdin) input+=chunk;
  const config=JSON.parse(input);
  if(config.url!=='http://127.0.0.1:20128') throw new Error('loopback only');
  const models=config.models||[];
  if(!config.createKey&&(typeof config.keyId!=='string'||!config.keyId||!models.length||!models.every(m=>typeof m==='string'&&m)))throw new Error('existing key id and model list required');
  const {apiFetch}=await import(pathToFileURL(join(config.package,'bin/cli/api.mjs')).href);
  async function api(path,method='GET',body){
    const r=await apiFetch(path,{baseUrl:config.url,method,body,retry:false,acceptNotOk:true,timeout:20000});
    if(!r.ok)throw new Error('HTTP '+r.status);
    return r.json();
  }
  const keyPath=config.createKey?null:'/api/keys/'+encodeURIComponent(config.keyId);
  // Every read happens before the first write, so a stopped server or refused read changes nothing.
  const providers=await api('/api/providers?limit=5000');
  const connections=(providers.connections||[]).filter(c=>c.provider==='openrouter' && c.isActive);
  if(!connections.some(c=>c.name==='main1'))throw new Error('main1 required');
  const numbered=connections.filter(c=>/^main[1-9][0-9]*$/.test(c.name));
  for(const c of numbered)if(numbered.filter(x=>x.name===c.name).length>1)throw new Error('ambiguous account name');
  const last=Math.max(...numbered.map(c=>Number(c.name.slice(4))));
  const rankOf=c=>/^main[1-9][0-9]*$/.test(c.name)?Number(c.name.slice(4)):Math.max(last+1,c.priority||last+1);
  const settings=await api('/api/settings');
  const keyBefore=keyPath?keyState(await api(keyPath)):null;
  if(keyBefore&&keyBefore.id!==config.keyId)throw new Error('key id mismatch');
  const before={providerStrategies:settings.providerStrategies||{},connections:connections.map(c=>({id:c.id,name:c.name,priority:c.priority})),created_key_id:null,key:keyBefore};
  await writeFile(config.backup,JSON.stringify(before,null,2),{mode:0o600});
  // The key goes first: if OmniRoute refuses it, nothing else has been written yet.
  const keyCurrent=keyBefore&&keyBefore.modelAccessMode==='restricted'&&sameList(keyBefore.allowedModels,models);
  let keyUpdated=false;
  if(keyBefore&&!keyCurrent){
    await api(keyPath,'PATCH',{modelAccessMode:'restricted',allowedModels:[...models].sort()});
    keyUpdated=true;
  }
  let secret, key_id=keyBefore?keyBefore.id:undefined;
  try{
    const strategies={...before.providerStrategies,openrouter:{...(before.providerStrategies.openrouter||{}),fallbackStrategy:'fill-first'}};
    if(JSON.stringify(strategies)!==JSON.stringify(before.providerStrategies))await api('/api/settings','PATCH',{providerStrategies:strategies});
    for(const c of connections){
      const rank=rankOf(c);
      if(c.priority!==rank)await api('/api/providers/'+encodeURIComponent(c.id),'PUT',{priority:rank});
    }
    if(config.createKey){
      const created=await api('/api/keys','POST',{name:'Claude Antigravity Kit '+Date.now(),modelAccessMode:'restricted',allowedModels:models,allowedCombos:[]});
      const key=typeof created.key==='object'?created.key:created;
      secret=typeof created.key==='string'?created.key:key.key||key.apiKey||created.apiKey;
      key_id=key.id||created.id;
      before.created_key_id=key_id;
      await writeFile(config.backup,JSON.stringify(before,null,2),{mode:0o600});
      if(!secret)throw new Error('missing key');
    }
    const verified=await api('/api/settings');
    if(verified.providerStrategies?.openrouter?.fallbackStrategy!=='fill-first')throw new Error('strategy verification');
    const rows=(await api('/api/providers?limit=5000')).connections.filter(c=>c.provider==='openrouter'&&c.isActive);
    if(rows.some(c=>c.priority!==rankOf(c)))throw new Error('priority verification');
    if(keyPath){
      const keyAfter=keyState(await api(keyPath));
      if(keyAfter.modelAccessMode!=='restricted'||!sameList(keyAfter.allowedModels,models))throw new Error('key verification');
    }
    process.stdout.write(JSON.stringify({secret,key_id,key_updated:keyUpdated,allowed_models:keyPath?models.length:undefined,
      connections:rows.map(c=>({id:c.id,name:c.name,priority:c.priority})),strategy:'fill-first'}));
  }catch(error){
    // Restore the key permissions recorded in the backup when a later step fails.
    if(keyUpdated){try{await api(keyPath,'PATCH',{modelAccessMode:keyBefore.modelAccessMode,allowedModels:keyBefore.allowedModels});}catch{}}
    throw error;
  }
}catch{process.stderr.write('OmniRoute pool setup failed.\n');process.exitCode=1;}
