function _smdMediaTokenParts(source, matchOffset, rawRef, parent){
  const value=String(source||'');
  const offset=Number(matchOffset)||0;
  const before=value.slice(0,offset);
  if(before.endsWith('"')||before.endsWith("'")||/(?:&quot;|&#39;)$/.test(before)){
    return _mediaTokenParts(value,offset,rawRef);
  }
  const prior=parent&&typeof parent.textContent==='string'?parent.textContent.slice(-1):'';
  return _mediaTokenParts(prior+value,prior.length+offset,rawRef);
}
