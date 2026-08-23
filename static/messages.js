      return normalized.endsWith('"')||normalized.endsWith("'")||/(?:&quot;|&#39;)$/.test(normalized)
        ? normalized
        : '';
    };
    const quotedRef=(candidate)=>String(candidate||'').replace(/&(?:amp;)?(quot|#39);?(?=[.,;:!?]*$)/,'&$1;');
    const localQuotedSource=quotedSource(before);
    if(localQuotedSource){
      return _mediaTokenParts(localQuotedSource,localQuotedSource.length,quotedRef(rawRef));
    }
