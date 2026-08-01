"""Multi-source paper search handlers.

Aggregates results from Semantic Scholar, arXiv, CrossRef, and OpenAlex.
Adapted from ScholarMind's search.py for the nanobot architecture.
"""

from __future__ import annotations

import asyncio
import re
from pathlib import Path

from loguru import logger
from websockets.http11 import Request as WsRequest
from websockets.http11 import Response

from nanobot.storage.storage_wrapper import StorageWrapper

from ..utils import (
    http_error,
    http_json_response,
    parse_mutation_data,
    parse_query,
)

# --- API endpoints ---
S2_API = "https://api.semanticscholar.org/graph/v1"
ARXIV_API = "https://export.arxiv.org/api/query"
CROSSREF_API = "https://api.crossref.org/works"
OPENALEX_API = "https://api.openalex.org/works"


# --- Search implementations ---

async def _search_semantic_scholar(query: str, limit: int = 20, offset: int = 0,
                                    year_from: int | None = None, year_to: int | None = None,
                                    author: str = "") -> dict:
    """Search Semantic Scholar with 429 retry."""
    import httpx

    params = {
        "query": query,
        "limit": min(limit, 100),
        "offset": offset,
        "fields": "title,authors,abstract,year,citationCount,venue,externalIds,openAccessPdf,url",
    }
    if year_from or year_to:
        year_range = f"{year_from or ''}-{year_to or ''}"
        params["year"] = year_range
    if author:
        params["query"] = f"{query} {author}"

    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(f"{S2_API}/paper/search", params=params)
                if resp.status_code == 429:
                    wait = 2 ** (attempt + 1)
                    logger.warning(f"S2 rate limited, waiting {wait}s")
                    await asyncio.sleep(wait)
                    continue
                resp.raise_for_status()
                data = resp.json()

                results = []
                for item in data.get("data", []):
                    pdf_url = None
                    oap = item.get("openAccessPdf")
                    if oap and isinstance(oap, dict):
                        pdf_url = oap.get("url")

                    authors = [a.get("name", "") for a in (item.get("authors") or [])]
                    ext_ids = item.get("externalIds") or {}
                    doi = ext_ids.get("DOI", "")

                    results.append({
                        "id": item.get("paperId", ""),
                        "title": item.get("title", ""),
                        "authors": authors,
                        "abstract": item.get("abstract", "") or "",
                        "year": item.get("year") or 0,
                        "citations": item.get("citationCount") or 0,
                        "pdfUrl": pdf_url,
                        "url": item.get("url", f"https://www.semanticscholar.org/paper/{item.get('paperId', '')}"),
                        "venue": item.get("venue", "") or "",
                        "doi": doi,
                        "source": "semantic_scholar",
                    })

                return {"results": results, "total": data.get("total", 0)}
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429 and attempt < 2:
                continue
            logger.error(f"S2 search error: {e}")
            return {"results": [], "total": 0}
        except Exception as e:
            logger.error(f"S2 search error: {e}")
            return {"results": [], "total": 0}

    return {"results": [], "total": 0}


async def _search_arxiv(query: str, limit: int = 20, offset: int = 0,
                         year_from: int | None = None, year_to: int | None = None,
                         author: str = "") -> dict:
    """Search arXiv API (XML-based)."""
    import httpx

    search_query = query
    if author:
        search_query = f"au:{author} AND {query}"

    params = {
        "search_query": f"all:{search_query}",
        "start": offset,
        "max_results": min(limit, 100),
        "sortBy": "relevance",
        "sortOrder": "descending",
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(ARXIV_API, params=params)
            resp.raise_for_status()
            xml_text = resp.text

            # Simple XML parsing
            results = []
            entries = xml_text.split("<entry>")[1:]  # skip feed header
            for entry in entries:
                title_m = re.search(r"<title>(.*?)</title>", entry, re.DOTALL)
                title = title_m.group(1).strip().replace("\n", " ") if title_m else ""

                summary_m = re.search(r"<summary>(.*?)</summary>", entry, re.DOTALL)
                abstract = summary_m.group(1).strip().replace("\n", " ") if summary_m else ""

                published_m = re.search(r"<published>(.*?)</published>", entry)
                year = 0
                if published_m:
                    try:
                        year = int(published_m.group(1)[:4])
                    except ValueError:
                        pass

                # Year filter
                if year_from and year < year_from:
                    continue
                if year_to and year > year_to:
                    continue

                # Authors
                authors = []
                for author_m in re.finditer(r"<name>(.*?)</name>", entry):
                    authors.append(author_m.group(1))

                # Links
                arxiv_id_m = re.search(r"<id>(.*?)</id>", entry)
                url = arxiv_id_m.group(1) if arxiv_id_m else ""
                pdf_url = None
                for link_m in re.finditer(r'<link[^>]*href="([^"]*)"[^>]*title="pdf"', entry):
                    pdf_url = link_m.group(1)
                    break

                # arXiv ID
                aid = ""
                if url:
                    aid = url.split("/abs/")[-1] if "/abs/" in url else url

                results.append({
                    "id": aid,
                    "title": title,
                    "authors": authors,
                    "abstract": abstract,
                    "year": year,
                    "citations": 0,
                    "pdfUrl": pdf_url,
                    "url": url,
                    "venue": "arXiv",
                    "doi": "",
                    "source": "arxiv",
                })

            return {"results": results, "total": len(results)}
    except Exception as e:
        logger.error(f"arXiv search error: {e}")
        return {"results": [], "total": 0}


async def _search_crossref(query: str, limit: int = 20, offset: int = 0,
                            year_from: int | None = None, year_to: int | None = None,
                            author: str = "") -> dict:
    """Search CrossRef API."""
    import httpx

    params = {
        "query.bibliographic": query,
        "rows": min(limit, 100),
        "offset": offset,
        "select": "DOI,title,author,published-print,abstract,is-referenced-by-count,container-title,link",
    }
    if author:
        params["query.author"] = author
    if year_from:
        params["from-pub-date"] = str(year_from)
    if year_to:
        params["until-pub-date"] = str(year_to)

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(CROSSREF_API, params=params)
            resp.raise_for_status()
            data = resp.json()

            results = []
            for item in data.get("message", {}).get("items", []):
                title_list = item.get("title", [])
                title = title_list[0] if title_list else ""
                # Strip HTML tags
                title = re.sub(r"<[^>]+>", "", title)

                abstract = item.get("abstract", "") or ""
                abstract = re.sub(r"<[^>]+>", "", abstract)

                authors = []
                for a in (item.get("author") or []):
                    name = f"{a.get('given', '')} {a.get('family', '')}".strip()
                    if name:
                        authors.append(name)

                year = 0
                dp = item.get("published-print") or item.get("published-online")
                if dp:
                    parts = dp.get("date-parts", [[]])[0]
                    if parts:
                        year = parts[0] or 0

                # Year filter (client-side)
                if year_from and year < year_from:
                    continue
                if year_to and year > year_to:
                    continue

                venue_list = item.get("container-title", [])
                venue = venue_list[0] if venue_list else ""

                pdf_url = None
                for link in (item.get("link") or []):
                    if link.get("content-type") == "application/pdf":
                        pdf_url = link.get("URL")
                        break

                doi = item.get("DOI", "")

                results.append({
                    "id": doi,
                    "title": title,
                    "authors": authors,
                    "abstract": abstract,
                    "year": year,
                    "citations": item.get("is-referenced-by-count") or 0,
                    "pdfUrl": pdf_url,
                    "url": f"https://doi.org/{doi}" if doi else "",
                    "venue": venue,
                    "doi": doi,
                    "source": "crossref",
                })

            total = data.get("message", {}).get("total-results", 0)
            return {"results": results, "total": total}
    except Exception as e:
        logger.error(f"CrossRef search error: {e}")
        return {"results": [], "total": 0}


async def _search_openalex(query: str, limit: int = 20, offset: int = 0,
                            year_from: int | None = None, year_to: int | None = None,
                            author: str = "") -> dict:
    """Search OpenAlex API."""
    import httpx

    params = {
        "search": query,
        "per_page": min(limit, 100),
        "page": (offset // limit) + 1,
        "sort": "relevance_score:desc",
        "select": "id,title,authorships,abstract_inverted_index,publication_year,cited_by_count,doi,open_access,primary_location,concepts,publication_date",
    }
    filters = ["type:article"]
    if year_from:
        filters.append(f"publication_year:{year_from}-2599")
    if year_to:
        filters.append(f"publication_year:1000-{year_to}")
    if author:
        filters.append(f"authorships.author.display_name.search:{author}")
    if filters:
        params["filter"] = ",".join(filters)

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(OPENALEX_API, params=params)
            resp.raise_for_status()
            data = resp.json()

            results = []
            for item in data.get("results", []):
                # Reconstruct abstract from inverted index
                abstract = ""
                aii = item.get("abstract_inverted_index")
                if aii and isinstance(aii, dict):
                    abstract = _reconstruct_abstract(aii)

                # Authors
                authors = []
                for a in (item.get("authorships") or [])[:5]:
                    name = a.get("author", {}).get("display_name", "")
                    if name:
                        authors.append(name)

                # PDF URL
                pdf_url = None
                oa = item.get("open_access") or {}
                pdf_url = oa.get("oa_url")
                if not pdf_url:
                    pl = item.get("primary_location") or {}
                    pdf_url = (pl.get("pdf_url") or "").strip() or None

                # Venue
                pl = item.get("primary_location") or {}
                source = pl.get("source") or {}
                venue = source.get("display_name", "") or ""

                # OpenAlex ID (extract short form)
                oa_id = (item.get("id") or "").replace("https://openalex.org/", "")

                doi = (item.get("doi") or "").replace("https://doi.org/", "")

                results.append({
                    "id": oa_id,
                    "title": item.get("title", "") or "",
                    "authors": authors,
                    "abstract": abstract,
                    "year": item.get("publication_year") or 0,
                    "citations": item.get("cited_by_count") or 0,
                    "pdfUrl": pdf_url,
                    "url": item.get("id", ""),
                    "venue": venue,
                    "doi": doi,
                    "source": "openalex",
                    "authorships": item.get("authorships") or [],
                    "concepts": item.get("concepts") or [],
                    "publicationDate": item.get("publication_date") or "",
                    "openAccess": item.get("open_access") or {},
                    "primaryLocation": item.get("primary_location") or {},
                })

            total = data.get("meta", {}).get("count", 0)
            return {"results": results, "total": total}
    except Exception as e:
        logger.error(f"OpenAlex search error: {e}")
        return {"results": [], "total": 0}


def _reconstruct_abstract(inverted_index: dict) -> str:
    """Reconstruct abstract text from OpenAlex inverted index format."""
    if not inverted_index:
        return ""
    word_positions = []
    for word, positions in inverted_index.items():
        for pos in positions:
            word_positions.append((pos, word))
    word_positions.sort(key=lambda x: x[0])
    return " ".join(w for _, w in word_positions)


# --- Handlers ---

async def handle_search_papers(
    request: WsRequest,
    storage: StorageWrapper,
    *,
    identity: dict[str, str],
) -> Response:
    """Search papers across multiple academic data sources."""
    query = parse_query(request.path)
    payload = parse_mutation_data(query)
    if isinstance(payload, Response):
        return payload

    search_query = payload.get("query", "").strip()
    if not search_query:
        return http_error(400, "query is required")

    source = payload.get("source", "openalex")
    limit = min(int(payload.get("limit", 20)), 100)
    offset = int(payload.get("offset", 0))
    year_from = payload.get("yearFrom")
    year_to = payload.get("yearTo")
    author = payload.get("author", "")

    year_from = int(year_from) if year_from else None
    year_to = int(year_to) if year_to else None

    source_map = {
        "semantic_scholar": _search_semantic_scholar,
        "arxiv": _search_arxiv,
        "crossref": _search_crossref,
        "openalex": _search_openalex,
    }

    search_fn = source_map.get(source, _search_openalex)
    result = await search_fn(search_query, limit=limit, offset=offset,
                              year_from=year_from, year_to=year_to, author=author)

    return http_json_response(result)


async def handle_import_paper(
    request: WsRequest,
    storage: StorageWrapper,
    *,
    identity: dict[str, str],
) -> Response:
    """Import a paper from a URL (download PDF, parse, and store)."""
    user_id = identity.get("user_id", "")
    role = identity.get("role", "researcher")
    if role != "researcher":
        return http_error(403, "Only researchers can import papers")
    query = parse_query(request.path)
    payload = parse_mutation_data(query)
    if isinstance(payload, Response):
        return payload

    pdf_url = payload.get("pdfUrl", "").strip()
    title = payload.get("title", "").strip()
    source = payload.get("source", "imported")
    source_id = payload.get("sourceId", "")
    authors = payload.get("authors", "")
    abstract = payload.get("abstract", "")
    year = int(payload.get("year", 0))
    doi = payload.get("doi", "")
    citations = int(payload.get("citations", 0))
    venue = payload.get("venue", "")

    if not pdf_url:
        return http_error(400, "pdfUrl is required")

    # Download PDF
    import httpx

    from nanobot.services.pdf_service import chunk_pages, extract_pdf_text

    upload_dir = Path.home() / ".nanobot" / "uploads" / "papers"
    upload_dir.mkdir(parents=True, exist_ok=True)

    import uuid
    file_name = f"{uuid.uuid4().hex[:12]}.pdf"
    file_path = upload_dir / file_name

    try:
        async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
            resp = await client.get(pdf_url)
            resp.raise_for_status()
            file_path.write_bytes(resp.content)
    except Exception as e:
        logger.error(f"PDF download failed: {e}")
        file_path.unlink(missing_ok=True)
        return http_error(500, f"PDF download failed: {str(e)}")

    # Extract text
    try:
        pdf_data = extract_pdf_text(file_path)
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        file_path.unlink(missing_ok=True)
        return http_error(500, f"PDF extraction failed: {str(e)}")

    if not title:
        title = pdf_data["title"]

    # Create paper record
    paper = await storage.create_paper({
        "title": title,
        "authors": authors if isinstance(authors, str) else ", ".join(authors) if isinstance(authors, list) else "",
        "abstract": abstract,
        "year": year,
        "doi": doi,
        "citation_count": citations,
        "venue": venue,
        "file_path": str(file_path),
        "file_name": file_name,
        "page_count": pdf_data["page_count"],
        "full_text": pdf_data["full_text"],
        "source": source,
        "source_id": source_id,
        "pdf_url": pdf_url,
        "user_id": user_id,
        "user_role": role,
    })

    # Create chunks
    chunks = chunk_pages(pdf_data["pages"])
    chunk_dicts = [
        {"chunk_index": c["chunk_index"], "page_number": c["page_number"], "content": c["content"]}
        for c in chunks
    ]
    chunk_count = await storage.create_paper_chunks(paper["id"], chunk_dicts)

    logger.info(f"Imported paper {paper['id']}: {title} ({pdf_data['page_count']} pages)")
    return http_json_response({
        "success": True,
        "paperId": paper["id"],
        "title": title,
        "pageCount": pdf_data["page_count"],
        "chunkCount": chunk_count,
        "message": "论文导入成功",
    })
