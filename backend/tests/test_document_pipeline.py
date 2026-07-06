"""Unit tests for document_pipeline.py (LLM and LaTeX compile mocked)."""

from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

import document_pipeline
import latex_service

VALID_TEX = "\\documentclass{article}\\begin{document}Hello\\end{document}"


def _job():
    return SimpleNamespace(
        id=1, role="Backend Engineer", company="TechCorp", location="London",
        parsed_skills=["Python"], parsed_requirements=["5 years"],
        parsed_responsibilities=["Build APIs"],
    )


@pytest.mark.unit
def test_extract_tex_from_fenced_response():
    response = f"Here is the document:\n```latex\n{VALID_TEX}\n```\nHope it helps!"
    assert document_pipeline._extract_tex(response) == VALID_TEX


@pytest.mark.unit
def test_extract_tex_missing_document():
    with pytest.raises(ValueError, match="no complete LaTeX document"):
        document_pipeline._extract_tex("sorry, I cannot do that")


@pytest.mark.unit
def test_generate_cv_happy_path():
    with patch("document_pipeline.llm.get_client", return_value=Mock()), \
         patch("document_pipeline.fit_evaluator.read_profile", return_value="profile"), \
         patch("document_pipeline.llm.complete", return_value=VALID_TEX), \
         patch("document_pipeline.latex_service.compile_tex",
               return_value=("uploads/generated/x.tex", "uploads/generated/x.pdf", 2)) as mock_compile:
        result = document_pipeline.generate_cv(_job(), blocks=[])

    assert result["checks"] == {"compiled": True, "page_count_ok": True}
    assert result["page_count"] == 2
    assert result["pdf_path"] == "uploads/generated/x.pdf"
    # draft + review passes, one compile
    assert mock_compile.call_count == 1
    assert mock_compile.call_args[0][2] == "lualatex"


@pytest.mark.unit
def test_generate_cover_letter_retries_on_wrong_page_count():
    compile_results = [
        ("t.tex", "t.pdf", 2),  # too long
        ("t.tex", "t.pdf", 1),  # fixed
    ]
    with patch("document_pipeline.llm.get_client", return_value=Mock()), \
         patch("document_pipeline.fit_evaluator.read_profile", return_value="profile"), \
         patch("document_pipeline.llm.complete", return_value=VALID_TEX) as mock_llm, \
         patch("document_pipeline.latex_service.compile_tex", side_effect=compile_results):
        result = document_pipeline.generate_cover_letter(_job(), blocks=[])

    assert result["page_count"] == 1
    assert result["checks"]["page_count_ok"] is True
    # One of the LLM calls must be the shortening prompt with cutting rules
    prompts = [call.args[1] for call in mock_llm.call_args_list]
    assert any("Cut the lowest-scoring lines first" in p for p in prompts)


@pytest.mark.unit
def test_generate_cv_retries_on_compile_error():
    effects = [
        latex_service.LatexCompileError("boom", log_excerpt="! Undefined control sequence"),
        ("t.tex", "t.pdf", 2),
    ]
    with patch("document_pipeline.llm.get_client", return_value=Mock()), \
         patch("document_pipeline.fit_evaluator.read_profile", return_value="profile"), \
         patch("document_pipeline.llm.complete", return_value=VALID_TEX) as mock_llm, \
         patch("document_pipeline.latex_service.compile_tex", side_effect=effects):
        result = document_pipeline.generate_cv(_job(), blocks=[])

    assert result["checks"]["compiled"] is True
    prompts = [call.args[1] for call in mock_llm.call_args_list]
    assert any("Undefined control sequence" in p for p in prompts)


@pytest.mark.unit
def test_generate_cv_empty_profile():
    with patch("document_pipeline.llm.get_client", return_value=Mock()), \
         patch("document_pipeline.fit_evaluator.read_profile", return_value=""):
        with pytest.raises(ValueError, match="profile is empty"):
            document_pipeline.generate_cv(_job(), blocks=[])
