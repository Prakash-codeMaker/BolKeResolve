"""Bounded, local text extraction for user-uploaded payment evidence.

The module reads only the already-uploaded file, never follows links or opens network
resources, and returns text to the caller for immediate redaction and rule-based parsing.
Raw extracted document text should not be persisted by callers.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

MAX_IMAGE_PIXELS = 18_000_000
MAX_PDF_PAGES = 5
MAX_TEXT_CHARS = 12_000


class EvidenceExtractionError(RuntimeError):
    """The file could not be safely or reliably read by the configured local tools."""


def _ocr_image(image: Any, *, language: str = "eng+hin") -> str:
    try:
        import pytesseract
    except Exception as exc:  # pragma: no cover - environment-dependent
        raise EvidenceExtractionError("Local OCR is not installed. You can still review the document manually.") from exc
    try:
        return str(pytesseract.image_to_string(image, lang=language, timeout=5) or "")[:MAX_TEXT_CHARS]
    except Exception as exc:
        # Do not include command lines, file paths, or raw content in public errors.
        raise EvidenceExtractionError("The image could not be read reliably. Please check it manually or upload a clearer image.") from exc


def extract_evidence_text(path: str | Path, mime_type: str) -> dict[str, Any]:
    """Extract a short text view from a PNG/JPEG/WEBP image or PDF.

    PDF parsing is limited to the first five pages. A scanned PDF is rendered locally
    for OCR when PyMuPDF and Tesseract are available. OCR is a candidate generator,
    not verification, and must be reviewed by the user.
    """
    file_path = Path(path)
    try:
        size = file_path.stat().st_size
    except OSError as exc:
        raise EvidenceExtractionError("This evidence file is no longer available.") from exc
    if size <= 0 or size > 8 * 1024 * 1024:
        raise EvidenceExtractionError("Evidence file size is outside the supported range.")

    if mime_type == "application/pdf" or file_path.suffix.lower() == ".pdf":
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(file_path), strict=False)
            if getattr(reader, "is_encrypted", False):
                raise EvidenceExtractionError("This PDF is password-protected. Please export an unlocked copy if you wish to review it.")
            pages = list(reader.pages[:MAX_PDF_PAGES])
            text = "\n".join((page.extract_text() or "") for page in pages)[:MAX_TEXT_CHARS]
            if len("".join(text.split())) >= 20:
                return {"text": text, "method": "pdf_text", "pages_read": len(pages), "truncated": len(reader.pages) > MAX_PDF_PAGES}
        except EvidenceExtractionError:
            raise
        except Exception:
            # Continue to local OCR fallback for scanned/image PDFs.
            text = ""
        try:
            import fitz
            import pytesseract
            from PIL import Image
            import io
            doc = fitz.open(str(file_path))
            if doc.needs_pass:
                raise EvidenceExtractionError("This PDF is password-protected. Please export an unlocked copy if you wish to review it.")
            snippets: list[str] = []
            page_limit = min(len(doc), MAX_PDF_PAGES, 3)
            for page_index in range(page_limit):
                page = doc.load_page(page_index)
                pix = page.get_pixmap(matrix=fitz.Matrix(1.35, 1.35), alpha=False)
                if pix.width * pix.height > MAX_IMAGE_PIXELS:
                    continue
                image = Image.open(io.BytesIO(pix.tobytes("png")))
                snippets.append(_ocr_image(image))
            text = "\n".join(snippets)[:MAX_TEXT_CHARS]
            if len("".join(text.split())) >= 12:
                return {"text": text, "method": "pdf_ocr", "pages_read": min(len(doc), 3), "truncated": len(doc) > 3}
        except EvidenceExtractionError:
            raise
        except Exception as exc:  # pragma: no cover - depends on deployment packages
            raise EvidenceExtractionError("This PDF has no readable text and local PDF OCR is unavailable. Please review it manually.") from exc
        raise EvidenceExtractionError("No reliable text could be extracted. You can still use the evidence file and review it manually.")

    if mime_type not in {"image/png", "image/jpeg", "image/webp"}:
        raise EvidenceExtractionError("This evidence format is not supported for automatic text review.")
    try:
        from PIL import Image, ImageOps
        with Image.open(file_path) as image:
            image.verify()
        with Image.open(file_path) as image:
            if image.width <= 0 or image.height <= 0 or image.width * image.height > MAX_IMAGE_PIXELS:
                raise EvidenceExtractionError("This image is too large to review safely. Please resize it and upload it again.")
            image = ImageOps.exif_transpose(image).convert("RGB")
            text = _ocr_image(image)
    except EvidenceExtractionError:
        raise
    except Exception as exc:
        raise EvidenceExtractionError("This image could not be opened safely. Please upload a valid PNG, JPG or WEBP file.") from exc
    if len("".join(text.split())) < 8:
        raise EvidenceExtractionError("The image text was not readable enough for a useful review. Try a clearer screenshot or review it manually.")
    return {"text": text[:MAX_TEXT_CHARS], "method": "image_ocr", "pages_read": 1, "truncated": len(text) > MAX_TEXT_CHARS}
