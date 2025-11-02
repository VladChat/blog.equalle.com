import re

def _norm_tag(s: str) -> str:
    s = (s or "").strip().lower()
    if not s:
        return ""
    out = []
    prev_dash = False
    for ch in s:
        if ch.isalnum():
            out.append(ch)
            prev_dash = False
        else:
            if not prev_dash:
                out.append("-")
                prev_dash = True
    t = "".join(out).strip("-")
    while "--" in t:
        t = t.replace("--", "-")
    return t[:40]

def _clean_phrase_for_meta(s: str) -> str:
    if not s:
        return ""
    s = re.sub(r"\s+", " ", str(s).strip())
    s = re.sub(r"^[,;|/]+", "", s)
    s = re.sub(r"[,;|/]+$", "", s)
    return s

def _smart_trim(text: str, limit: int = 60) -> str:
    if len(text) <= limit:
        return text
    cut = text[:limit]
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut.rstrip(" -–—")
