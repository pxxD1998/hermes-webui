function _mediaTokenParts(source, matchOffset, rawRef){
  let ref=String(rawRef||'');
  let suffix='';
  const before=String(source||'').slice(0,Number(matchOffset)||0);
  // Quotes are valid path/URL bytes, so detach one only when the prose has the
  // same opener immediately before MEDIA:. The entity forms are what the real
  // streaming parser passes after escaping text nodes.
  for(const family of [
    {value:'"', forms:['"','&quot;']},
    {value:"'", forms:["'",'&#39;']},
  ]){
    if(!family.forms.some(form=>before.endsWith(form))) continue;
    let quote='', closeAt=-1;
    for(const form of family.forms){
      const index=ref.lastIndexOf(form);
      if(index>closeAt){ quote=form; closeAt=index; }
    }
    if(closeAt<=0) continue;
    const afterQuote=ref.slice(closeAt+quote.length);
    if(!/^[.,;:!?]*$/.test(afterQuote)) continue;
    ref=ref.slice(0,closeAt);
    suffix=family.value+afterQuote;
    break;
  }
  const trailingPunctuation=ref.match(/[.,;:!?]+$/)?.[0]||'';
  for(const delimiter of ['***','___','**','__','*','_','`']){
    if(!before.endsWith(delimiter)) continue;
    let candidate=ref;
    let afterDelimiter='';
    if(trailingPunctuation&&candidate.slice(0,-trailingPunctuation.length).endsWith(delimiter)){
      candidate=candidate.slice(0,-trailingPunctuation.length);
      afterDelimiter=trailingPunctuation;
    }
    if(candidate.endsWith(delimiter)&&candidate.length>delimiter.length){
      ref=candidate.slice(0,-delimiter.length);
      suffix=delimiter+afterDelimiter;
      break;
    }
  }
  const remoteValue=/^https?:\/\//i.test(ref);
  const punctuation=remoteValue?null:ref.match(/[.,;:!?]+$/);
  if(punctuation&&ref.length>punctuation[0].length){
    ref=ref.slice(0,-punctuation[0].length);
    suffix=punctuation[0]+suffix;
  }
  if(!ref||/^[*_`]+$/.test(ref)) return null;
  return [ref,suffix];
}
