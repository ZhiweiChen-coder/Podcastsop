from __future__ import annotations

from io import BytesIO
from typing import Literal, Tuple


def read_uploaded_file(filename: str, data: bytes) -> Tuple[str, Literal["docx", "txt", "srt"]]:
    ext = filename.split(".")[-1].lower()
    if ext not in ("docx", "txt", "srt"):
        raise ValueError(f"Unsupported file type: {ext}")

    if ext == "txt":
        # best-effort: utf-8 first, fallback latin-1
        try:
            return data.decode("utf-8"), "txt"
        except UnicodeDecodeError:
            return data.decode("latin-1"), "txt"

    if ext == "docx":
        try:
            from docx import Document  # type: ignore
        except Exception as e:
            raise RuntimeError("Missing dependency for .docx. Please install: python-docx") from e

        doc = Document(BytesIO(data))
        text = "\n".join(p.text for p in doc.paragraphs)
        return text.strip(), "docx"

    try:
        import srt  # type: ignore
    except Exception as e:
        raise RuntimeError("Missing dependency for .srt. Please install: srt") from e

    subs = list(srt.parse(data.decode("utf-8", errors="replace")))
    lines = []
    for sub in subs:
        content = (sub.content or "").strip()
        if content:
            lines.append(content)
    return "\n".join(lines).strip(), "srt"

