def split_media_token_ref(text: str, match) -> tuple[str, str] | None:
    """Split a MEDIA regex match into its clean ref and detached prose suffix."""
    ref = str(match.group(1) or "")
    suffix = ""
    before = str(text or "")[: match.start()]
    for quote in ('"', "'"):
        if not before.endswith(quote):
            continue
        close_at = ref.rfind(quote)
        if close_at <= 0:
            continue
        after_quote = ref[close_at + 1 :]
        if not _re.fullmatch(r"[.,;:!?]*", after_quote):
            continue
        ref = ref[:close_at]
        suffix = quote + after_quote
        break
    punctuation = _re.search(r"[.,;:!?]+$", ref)
    if punctuation and len(ref) > len(punctuation.group(0)):
        ref = ref[: punctuation.start()]
        suffix = punctuation.group(0) + suffix
    for delimiter in ("***", "___", "**", "__", "*", "_", "`"):
        if before.endswith(delimiter) and ref.endswith(delimiter) and len(ref) > len(delimiter):
            ref = ref[: -len(delimiter)]
            suffix = delimiter + suffix
            break
    if not ref or _re.fullmatch(r"[*_`]+", ref):
        return None
    return ref, suffix
