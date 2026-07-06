"""LaTeX compilation for generated CVs and cover letters.

CVs compile with lualatex (moderncv), cover letters with xelatex
(cover.cls needs fontspec). Compilation happens in a temp dir seeded
with cover.cls and the OpenFonts directory; the resulting .tex and .pdf
are copied to uploads/generated/ so the existing /uploads static mount
serves them.
"""

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Tuple

from pypdf import PdfReader

TEMPLATES_DIR = Path(__file__).parent / "templates"
OUTPUT_DIR = Path(__file__).parent / "uploads" / "generated"


class LatexNotInstalled(RuntimeError):
    pass


class LatexCompileError(RuntimeError):
    def __init__(self, message: str, log_excerpt: str):
        super().__init__(message)
        self.log_excerpt = log_excerpt


def compile_tex(tex_source: str, stem: str, engine: str) -> Tuple[str, str, int]:
    """Compile tex_source and return (tex_relpath, pdf_relpath, page_count).

    Paths are relative to the backend dir (e.g. "uploads/generated/x.pdf")
    so they slot into the existing file-link handling.
    """
    if shutil.which(engine) is None:
        raise LatexNotInstalled(
            f"{engine} is not installed. Install a TeX distribution (e.g. TeX Live) to compile documents."
        )

    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        (tmpdir / f"{stem}.tex").write_text(tex_source, encoding="utf-8")
        shutil.copy(TEMPLATES_DIR / "cover.cls", tmpdir)
        shutil.copytree(TEMPLATES_DIR / "OpenFonts", tmpdir / "OpenFonts")

        result = subprocess.run(
            [engine, "-interaction=nonstopmode", f"{stem}.tex"],
            cwd=tmpdir,
            capture_output=True,
            text=True,
            timeout=120,
        )

        pdf_path = tmpdir / f"{stem}.pdf"
        if not pdf_path.exists():
            log = result.stdout or ""
            # The useful error is near the end of the log
            raise LatexCompileError(
                f"{engine} failed to produce a PDF", log_excerpt=log[-2000:]
            )

        page_count = len(PdfReader(pdf_path).pages)

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        final_tex = OUTPUT_DIR / f"{stem}.tex"
        final_pdf = OUTPUT_DIR / f"{stem}.pdf"
        final_tex.write_text(tex_source, encoding="utf-8")
        shutil.copy(pdf_path, final_pdf)

    backend_dir = Path(__file__).parent
    return (
        str(final_tex.relative_to(backend_dir)),
        str(final_pdf.relative_to(backend_dir)),
        page_count,
    )
