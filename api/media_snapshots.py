    import re as _re
    from api.helpers import split_media_token_ref

    if resolve_ref is None:
        resolve_ref = resolve_media_ref
    if allowed_predicate is None:
        allowed_predicate = media_capture_allowed
    media_re = _re.compile(r"MEDIA:([^\s\)\]]+)")
    captured = 0
    for msg in messages or []:
        if not isinstance(msg, dict) or msg.get("role") != "assistant":
            continue
        content = msg.get("content")
        if not isinstance(content, str) or "MEDIA:" not in content:
            continue
        matches = list(media_re.finditer(content))
        if not matches:
            continue
        existing = msg.get("_media_snapshots")
        snaps = dict(existing) if isinstance(existing, dict) else {}
        changed = False
        for match in matches:
            parts = split_media_token_ref(content, match)
            if not parts:
                continue
            raw_ref, _suffix = parts
            raw_ref = raw_ref.strip()
            if not raw_ref:
                continue
            if resolve_ref is not None:
                try:
                    path = resolve_ref(raw_ref)
                except Exception:
                    path = None
            else:
                path = None
            if path is None:
                continue
            # Index by BOTH the resolved absolute path and the raw token as the
            # frontend embeds it (file:// unwrapped, ~/ kept verbatim). One of
            # the two always matches the path= query param in the rendered URL.
            keys = [str(path)]
            if raw_ref not in keys:
                keys.append(raw_ref)
            # A recorded digest is FINAL once stamped (blob presence is NOT
            # re-checked): quota eviction must not cause a re-settle to
            # re-capture the current live bytes and rebind the historical
            # message — that would defeat per-message immutability and thrash
            # the store with re-capture I/O. Evicted blobs simply fall back to
            # live-file serving on the serve side.
            pending = [k for k in keys if not (snaps.get(k) and is_valid_digest(snaps[k]))]
            if not pending:
                continue  # already stored under every key — zero-I/O fast path
            if allowed_predicate is not None:
                try:
                    if not allowed_predicate(path):
                        continue
                except Exception:
                    continue
            digest = capture_snapshot(path)
            if digest:
                for k in keys:
                    snaps[k] = digest
                changed = True
                captured += 1
        if changed:
            msg["_media_snapshots"] = snaps
    return captured
