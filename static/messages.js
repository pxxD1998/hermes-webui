function _smdMediaTokenParts(source, matchOffset, rawRef, parent){
    const value=String(source||'');
    const offset=Number(matchOffset)||0;
    const before=value.slice(0,offset);
    const quotedSource=(candidate)=>{
      const normalized=String(candidate||'').replace(/&amp;(quot;|#39;)$/,'&$1');
      return normalized.endsWith('"')||normalized.endsWith("'")||/(?:&quot;|&#39;)$/.test(normalized)
        ? normalized
        : '';
    };
    const quotedRef=(candidate)=>String(candidate||'').replace(/&(?:amp;)?(quot|#39);?(?=[.,;:!?]*$)/,'&$1;');
    const localQuotedSource=quotedSource(before);
    if(localQuotedSource){
      return _mediaTokenParts(localQuotedSource,localQuotedSource.length,quotedRef(rawRef));
    }
    // Keep enough same-owner context to reconstruct a split parser-escaped
    // HTML-entity quote opener. &amp;quot; is the longest accepted form
    // (10 chars); literal and singly encoded quotes are shorter.
    const prior=parent&&typeof parent.textContent==='string'?parent.textContent.slice(-10):'';
    const contextQuotedSource=quotedSource(prior);
    if(contextQuotedSource){
      return _mediaTokenParts(contextQuotedSource,contextQuotedSource.length,quotedRef(rawRef));
    }
    return _mediaTokenParts(prior+value,prior.length+offset,rawRef);
  }