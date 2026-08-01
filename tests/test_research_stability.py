from pypdf import PdfReader

from nanobot.api.handlers.papers import _owns as owns_paper
from nanobot.api.handlers.research_exports import _csv_response, _docx, _pdf


def test_paper_ownership_requires_user_and_role():
    paper = {"userId": "researcher-a", "userRole": "researcher"}
    assert owns_paper(paper, {"user_id": "researcher-a", "role": "researcher"})
    assert not owns_paper(paper, {"user_id": "researcher-b", "role": "researcher"})
    assert not owns_paper(paper, {"user_id": "researcher-a", "role": "teacher"})


def test_exports_are_real_files():
    docx = _docx("# 标题\n\n正文")
    assert docx.startswith(b"PK")
    pdf = _pdf("# title\n\nbody")
    assert len(PdfReader(__import__("io").BytesIO(pdf)).pages) == 1
    response = _csv_response("table", {"columns": [{"key": "name", "label": "名称"}], "rows": [{"name": "中文"}]})
    assert response.body.startswith(b"\xef\xbb\xbf")
    assert b"\xe4\xb8\xad\xe6\x96\x87" in response.body
