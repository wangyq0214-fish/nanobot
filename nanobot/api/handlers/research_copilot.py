"""Evidence-bound paper Copilot endpoint."""

from __future__ import annotations

import asyncio
from typing import Any

from loguru import logger
from websockets.http11 import Request as WsRequest
from websockets.http11 import Response

from nanobot.storage.storage_wrapper import StorageWrapper

from ..llm_utils import make_llm_provider
from ..utils import http_error, http_json_response, parse_request_mutation


async def handle_paper_copilot(request: WsRequest, storage: StorageWrapper, paper_id: str, *, identity: dict[str, str]) -> Response:
    if identity.get("role") != "researcher":
        return http_error(403, "Only researchers can use paper Copilot")
    paper = await storage.get_paper(int(paper_id))
    if not paper or (paper.get("userId") or paper.get("user_id")) != identity.get("user_id") or (paper.get("userRole") or paper.get("user_role") or "researcher") != identity.get("role"):
        return http_error(404, "Paper not found")
    payload = await parse_request_mutation(request)
    if isinstance(payload, Response):
        return payload
    message = str(payload.get("message", "")).strip()
    if not message:
        return http_error(400, "message is required")
    chunks = await storage.get_paper_chunks(int(paper_id))
    terms = {term.lower() for term in message.split() if len(term) > 1}
    ranked = sorted(chunks, key=lambda chunk: sum(term in chunk.get("content", "").lower() for term in terms), reverse=True)
    evidence = [chunk for chunk in ranked if any(term in chunk.get("content", "").lower() for term in terms)][:6]
    if not evidence:
        return http_json_response({"answer": "未找到足够证据，无法基于这篇论文确认该问题。", "citations": [], "insufficientEvidence": True})
    context = "\n\n".join(f"[C{index + 1}] 第{chunk.get('pageNumber', 0)}页：{chunk.get('content', '')[:1800]}" for index, chunk in enumerate(evidence))
    prompt = f"""你是论文证据型 Copilot。只能使用下面的论文分片回答问题，不得补全分片中没有的事实。每个关键结论必须在句末标注对应证据编号，例如 [C1]；证据不足时明确说未找到足够证据。\n\n问题：{message}\n\n证据：\n{context}"""
    try:
        provider, model = make_llm_provider()
        response = await asyncio.wait_for(provider.chat_stream(messages=[{"role": "user", "content": prompt}], model=model, temperature=0.1), timeout=120)
        answer = (response.content or "").strip()
    except Exception as exc:
        logger.exception("Paper Copilot failed")
        return http_error(502, f"Copilot 调用失败：{exc}")
    citations = [{
        "paperId": int(paper_id), "chunkId": chunk["id"], "pageNumber": chunk.get("pageNumber", 0),
        "quote": chunk.get("content", "")[:500], "relevance": round(max(0.1, 1 - index * 0.1), 2),
    } for index, chunk in enumerate(evidence)]
    return http_json_response({"answer": answer, "citations": citations, "insufficientEvidence": False})
