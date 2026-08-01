from pathlib import Path

from nanobot.agent.context import ContextBuilder


def test_latex_writing_context_escapes_document_braces():
    builder = ContextBuilder(Path("."))

    context = builder.build_latex_writing_context(
        {
            "_skill": "latex-writing",
            "file_path": "document.tex",
            "latex_code": "\\documentclass{article}\n\\begin{document}\nHi\n\\end{document}",
        }
    )

    assert "\\documentclass" in context
    assert "\\begin{document}" in context
    assert "\\end{document}" in context
