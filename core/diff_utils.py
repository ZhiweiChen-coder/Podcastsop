from __future__ import annotations

import difflib
from html import escape
from typing import Literal


def diff_html(a: str, b: str, *, granularity: Literal["line", "word"] = "line") -> str:
    """
    Returns a simple HTML diff view.
    - line: compare by lines
    - word: compare by whitespace-delimited tokens (MVP)
    """
    if granularity == "word":
        a_seq = a.split()
        b_seq = b.split()
    else:
        a_seq = a.splitlines()
        b_seq = b.splitlines()

    sm = difflib.SequenceMatcher(a=a_seq, b=b_seq)

    out = [
        "<div style='font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, \"Liberation Mono\", \"Courier New\", monospace; font-size: 13px; line-height: 1.5;'>"
    ]
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            chunk = a_seq[i1:i2]
            out.append(_wrap(chunk, color="#111827"))
        elif tag == "delete":
            chunk = a_seq[i1:i2]
            out.append(_wrap(chunk, color="#991B1B", bg="#FEE2E2", prefix="- "))
        elif tag == "insert":
            chunk = b_seq[j1:j2]
            out.append(_wrap(chunk, color="#065F46", bg="#D1FAE5", prefix="+ "))
        else:  # replace
            chunk_a = a_seq[i1:i2]
            chunk_b = b_seq[j1:j2]
            out.append(_wrap(chunk_a, color="#991B1B", bg="#FEE2E2", prefix="- "))
            out.append(_wrap(chunk_b, color="#065F46", bg="#D1FAE5", prefix="+ "))
    out.append("</div>")
    return "\n".join(out)


def _wrap(seq, *, color: str, bg: str | None = None, prefix: str = "") -> str:
    if not seq:
        return ""
    style = f"color:{color};"
    if bg:
        style += f"background:{bg};"
    safe = escape("\n".join(f"{prefix}{s}" for s in seq))
    return f"<pre style='margin:0; padding:8px; white-space:pre-wrap; {style}'>{safe}</pre>"

