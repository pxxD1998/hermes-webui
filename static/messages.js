  function _smdMediaTokenParts(source, matchOffset, rawRef, parent){
    const value=String(source||'');
    const offset=Number(matchOffset)||0;
    const before=value.slice(0,offset);
    if(before.endsWith('"')||before.endsWith("'")||/(?:&quot;|&#39;)$/.test(before)){
      return _mediaTokenParts(value,offset,rawRef);
    }
    // Keep enough same-owner context to reconstruct a split HTML-entity quote
    // opener. &quot; is the longest supported form (6 chars); literal quotes and
    // &#39; are shorter and are covered by the same lookbehind window.
    const prior=parent&&typeof parent.textContent==='string'?parent.textContent.slice(-6):'';
    return _mediaTokenParts(prior+value,prior.length+offset,rawRef);
  }
