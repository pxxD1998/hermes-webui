def split_media_token_ref(text: str, match) -> tuple[str, str] | None:
    """Split a MEDIA regex match into its clean ref and detached prose suffix."""
    ref = str(match.group(1) or "")
    suffix = ""
    before = str(text or "")[: match.start()]
    for value, forms in (
        ('"', ('"', "&quot;")),
        ("'", ("'", "&#39;")),
    ):
        if not any(before.endswith(form) for form in forms):
            continue
        close_form = ""
        close_at = -1
        for form in forms:
            index = ref.rfind(form)
            if index > close_at:
                close_form = form
                close_at = index
        if close_at <= 0:
            continue
        after_quote = ref[close_at + len(close_form) :]
        if not _re.fullmatch(r"[.,;:!?]*", after_quote):
            continue
        ref = ref[:close_at]
        suffix = value + after_quote
        break
    trailing_match = _re.search(r"[.,;:!?]+$", ref)
    trailing_punctuation = trailing_match.group(0) if trailing_match else ""
    for delimiter in ("***", "___", "**", "__", "*", "_", "`"):
        if not before.endswith(delimiter):
            continue
        candidate = ref
        after_delimiter = ""
        if trailing_punctuation and candidate[: -len(trailing_punctuation)].endswith(delimiter):
            candidate = candidate[: -len(trailing_punctuation)]
            after_delimiter = trailing_punctuation
        if candidate.endswith(delimiter) and len(candidate) > len(delimiter):
            ref = candidate[: -len(delimiter)]
            suffix = delimiter + after_delimiter + suffix
            break
    is_remote = bool(_re.match(r"^https?://", ref, _re.IGNORECASE))
    punctuation = None if is_remote else _re.search(r"[.,;:!?]+$", ref)
    if punctuation and len(ref) > len(punctuation.group(0)):
        ref = ref[: punctuation.start()]
        suffix = punctuation.group(0) + suffix
    if not ref or _re.fullmatch(r"[*_`]+", ref):
        return None
    return ref, suffix
