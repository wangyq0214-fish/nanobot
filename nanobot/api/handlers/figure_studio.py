"""Figure Studio API: data inspection, template compatibility, and previews."""

from __future__ import annotations

import base64
import csv
import io
import json
import math
import uuid
from pathlib import Path
from typing import Any

from websockets.http11 import Request as WsRequest
from websockets.http11 import Response

from ..utils import http_error, http_json_response, http_response, parse_request_mutation

FIGURE_TEMPLATES = [
    {"id": "volcano", "category": "数据分析图", "name": "火山图", "description": "展示效应大小与显著性", "required": {"gene": "categorical", "effect": "numeric", "pvalue": "numeric"}},
    {"id": "roc", "category": "数据分析图", "name": "ROC 曲线", "description": "比较分类模型性能", "required": {"fpr": "numeric", "tpr": "numeric"}},
    {"id": "dotplot", "category": "数据分析图", "name": "表达点图", "description": "用点大小和颜色展示矩阵", "required": {"row": "categorical", "column": "categorical", "size": "numeric", "color": "numeric"}},
    {"id": "marginal", "category": "数据分析图", "name": "边际分布图", "description": "散点图加边际分布", "required": {"x": "numeric", "y": "numeric"}, "optional": {"group": "categorical"}},
    {"id": "paired", "category": "数据分析图", "name": "配对数据图", "description": "展示同一样本前后变化", "required": {"subject": "categorical", "condition": "categorical", "value": "numeric"}},
    {"id": "grouped_bar", "category": "常规统计图", "name": "分组柱状图", "description": "比较分类与实验组的均值", "required": {"category": "categorical", "group": "categorical", "value": "numeric"}, "optional": {"error": "numeric"}},
    {"id": "boxplot", "category": "常规统计图", "name": "箱线图", "description": "展示组间分布和离群值", "required": {"category": "categorical", "value": "numeric"}},
    {"id": "scatter", "category": "常规统计图", "name": "散点图", "description": "展示两个连续变量的关系", "required": {"x": "numeric", "y": "numeric"}, "optional": {"group": "categorical"}},
    {"id": "line", "category": "常规统计图", "name": "折线图", "description": "展示时间、数字或顺序趋势", "required": {"x": "any", "y": "numeric", "group": "categorical"}, "optional": {"event": "categorical"}},
    {"id": "heatmap", "category": "常规统计图", "name": "热图", "description": "支持 row-column-value 长表并转换为二维数值矩阵", "required": {"row": "categorical", "column": "categorical", "value": "numeric"}},
    {"id": "forest", "category": "科研组合图", "name": "森林图", "description": "展示效应量和置信区间", "required": {"label": "categorical", "effect": "numeric", "lower": "numeric", "upper": "numeric"}},
    {"id": "multi_panel", "category": "科研组合图", "name": "多面板组合图", "description": "按面板字段拆分并组合实验结果", "required": {"panel": "categorical", "category": "categorical", "value": "numeric"}},
    {"id": "mechanism_schematic", "category": "概念示意图", "name": "机制示意图", "description": "根据文字生成论文概念图", "required": {}},
    {"id": "graphical_abstract", "category": "概念示意图", "name": "图形摘要", "description": "根据研究内容生成图形摘要", "required": {}},
]

TEMPLATE_PREVIEWS = {
    "grouped_bar": "chart-atlas/atlas-01-bar-charts.png",
    "line": "chart-atlas/atlas-02-line-trends.png",
    "heatmap": "chart-atlas/atlas-03-heatmaps.png",
    "scatter": "chart-atlas/atlas-04-scatter-bubble.png",
    "marginal": "chart-atlas/atlas-04-scatter-bubble.png",
    "roc": "chart-atlas/atlas-02-line-trends.png",
    "boxplot": "chart-atlas/atlas-06-distributions.png",
    "paired": "chart-atlas/atlas-06-distributions.png",
    "volcano": "chart-atlas/atlas-04-scatter-bubble.png",
    "dotplot": "chart-atlas/atlas-10-network-matrix.png",
    "forest": "chart-atlas/atlas-07-forest-interval.png",
    "multi_panel": "gallery/fig5-validation-perturbation-rich.png",
    "mechanism_schematic": "gallery/fig1-material-mechanism-rich.png",
    "graphical_abstract": "gallery/fig4-single-cell-systems-rich.png",
}


def _figure_assets_root() -> Path:
    return Path(__file__).resolve().parents[3] / ".nanobot" / "templates" / "researcher" / "skills" / "nature-figure" / "assets"

def _recommend_mapping(schema: dict[str, Any], template_id: str) -> dict[str, Any]:
    """Deterministically normalize user columns; this is the AI adapter seam."""
    columns = schema.get("columns", [])
    names = [str(item.get("name", "")) for item in columns]
    types = {str(item.get("name", "")): item.get("type") for item in columns}
    used: set[str] = set()

    def pick(kind: str, hints: tuple[str, ...], *, reuse: bool = False) -> str | None:
        candidates = [n for n in names if (kind == "any" or types.get(n) == kind) and (reuse or n not in used)]
        for hint in hints:
            for name in candidates:
                if hint in name.lower():
                    used.add(name)
                    return name
        if candidates:
            used.add(candidates[0])
            return candidates[0]
        return None

    def fields(specs: tuple[tuple[str, str, tuple[str, ...]], ...]) -> dict[str, str | None]:
        return {role: pick(kind, hints) for role, kind, hints in specs}

    if template_id == "volcano":
        return fields((("gene", "categorical", ("gene", "symbol", "基因", "名称")), ("effect", "numeric", ("log2", "fc", "fold", "effect", "效应", "倍数")), ("pvalue", "numeric", ("padj", "pval", "pvalue", "fdr", "显著", "校正"))))
    if template_id == "roc":
        result = fields((("fpr", "numeric", ("fpr", "false", "假阳")),))
        result["tpr"] = [name for name in names if types.get(name) == "numeric" and name != result["fpr"]]
        return result
    if template_id == "dotplot":
        return fields((("row", "categorical", ("cell", "type", "row", "行", "细胞")), ("column", "categorical", ("gene", "column", "列", "基因")), ("size", "numeric", ("pct", "percent", "size", "比例", "大小")), ("color", "numeric", ("avg", "scaled", "color", "表达", "颜色"))))
    if template_id in {"marginal", "scatter"}:
        result = fields((("x", "numeric", ("x", "time", "时间")), ("y", "numeric", ("y", "value", "数值")), ("group", "categorical", ("group", "condition", "组", "条件"))))
        return {key: value for key, value in result.items() if value}
    if template_id == "paired":
        return fields((("subject", "categorical", ("subject", "sample", "id", "样本", "编号")), ("condition", "categorical", ("condition", "before", "after", "条件", "时期")), ("value", "numeric", ("value", "measurement", "数值", "测量"))))
    if template_id == "grouped_bar":
        return fields((("category", "categorical", ("category", "分类", "类别", "时间", "剂量")), ("group", "categorical", ("group", "condition", "treatment", "组别", "分组", "处理")), ("value", "numeric", ("value", "mean", "数值", "均值", "测量")), ("error", "numeric", ("error", "err", "sd", "sem", "误差", "标准差", "标准误"))))
    if template_id == "heatmap":
        return fields((("row", "categorical", ("row", "gene", "行", "行分类", "基因")), ("column", "categorical", ("column", "condition", "列", "列分类", "条件")), ("value", "numeric", ("value", "expression", "数值", "表达", "表达值"))))
    if template_id == "multi_panel":
        return fields((("panel", "categorical", ("panel", "facet", "面板")), ("category", "categorical", ("category", "group", "分类", "组别")), ("value", "numeric", ("value", "数值"))))
    if template_id == "forest":
        return fields((("label", "categorical", ("label", "subgroup", "项目", "亚组")), ("effect", "numeric", ("effect", "estimate", "效应", "估计")), ("lower", "numeric", ("lower", "low", "下限")), ("upper", "numeric", ("upper", "high", "上限"))))
    if template_id == "line":
        result = fields((("x", "any", ("time", "date", "month", "x", "时间", "剂量")), ("y", "numeric", ("value", "y", "count", "数值")), ("group", "categorical", ("group", "condition", "组", "条件")), ("event", "categorical", ("event", "annotation", "label", "事件", "标注"))))
        return {key: value for key, value in result.items() if value}
    return fields((("category", "categorical", ("category", "group", "condition", "分类", "组别")), ("value", "numeric", ("value", "mean", "数值", "均值")), ("group", "categorical", ("group", "condition", "treatment", "分组", "处理"))))


async def _body(request: WsRequest) -> dict[str, Any] | Response:
    try:
        return await parse_request_mutation(request)
    except Exception as exc:
        return http_error(400, f"invalid JSON body: {exc}")


def _decode(data: str) -> bytes:
    if "," in data and data.startswith("data:"):
        data = data.split(",", 1)[1]
    return base64.b64decode(data)


def _inspect_csv(raw: bytes) -> dict[str, Any]:
    text = raw.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    fields = reader.fieldnames or []
    rows = list(reader)
    columns = []
    for field in fields:
        values = [row.get(field, "") for row in rows]
        nonempty = [value for value in values if value not in (None, "")]
        numeric = 0
        for value in nonempty:
            try:
                float(value)
                numeric += 1
            except (TypeError, ValueError):
                pass
        kind = "numeric" if nonempty and numeric == len(nonempty) else "categorical"
        columns.append({"name": field, "type": kind, "missing": len(values) - len(nonempty), "unique": len(set(nonempty))})
    return {"rows": len(rows), "columns": columns, "preview": rows[:20]}


def _mapping_errors(template: dict[str, Any], mapping: dict[str, Any], schema: dict[str, Any], params: dict[str, Any] | None = None) -> list[str]:
    columns = {item["name"]: item for item in schema.get("columns", [])}
    types = {name: item.get("type") for name, item in columns.items()}
    errors: list[str] = []
    check_missing_roles = set(template.get("required", {}))
    if template.get("id") == "grouped_bar" and str((params or {}).get("errorBar", "SEM")).lower() not in {"none", "不显示"}:
        check_missing_roles.add("error")
    for role, kind in template.get("required", {}).items():
        if template.get("id") == "line" and role == "x":
            kind = "any"
        selected = mapping.get(role)
        values = selected if isinstance(selected, list) else [selected]
        values = [value for value in values if value]
        if not values:
            errors.append(f"{role} 字段未映射")
        elif kind != "any" and any(types.get(value) != kind for value in values):
            errors.append(f"{role} 需要映射到{('数值' if kind == 'numeric' else '分类')}字段")
        elif any(int(columns[value].get("missing") or 0) > 0 for value in values if role in check_missing_roles):
            errors.append(f"{role} 字段存在缺失值")
    for role, kind in template.get("optional", {}).items():
        if template.get("id") == "line" and role == "x":
            kind = "any"
        selected = mapping.get(role)
        if selected and kind != "any" and types.get(selected) != kind:
            errors.append(f"{role} 需要映射到{('数值' if kind == 'numeric' else '分类')}字段")
        elif selected and role in check_missing_roles and int(columns.get(selected, {}).get("missing") or 0) > 0:
            errors.append(f"{role} 字段存在缺失值")
    return errors


def _validate_scatter_csv(path: str | Path, mapping: dict[str, Any], params: dict[str, Any] | None = None) -> list[str]:
    x_col = mapping.get("x")
    y_col = mapping.get("y")
    group_col = mapping.get("group") or None
    errors: list[str] = []
    if not x_col or not y_col:
        return errors
    try:
        with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            fields = set(reader.fieldnames or [])
            missing_columns = [column for column in (x_col, y_col, group_col) if column and column not in fields]
            if missing_columns:
                return [f"scatter CSV 缺少字段: {', '.join(str(column) for column in missing_columns)}"]
            rows = list(reader)
    except OSError as exc:
        return [f"scatter CSV 无法读取: {exc}"]

    invalid_numeric_rows: list[int] = []
    missing_group_rows: list[int] = []
    valid_points: list[tuple[float, float, str]] = []
    for row_number, row in enumerate(rows, start=2):
        try:
            x_value = float(str(row.get(str(x_col), "")).strip())
            y_value = float(str(row.get(str(y_col), "")).strip())
            if not math.isfinite(x_value) or not math.isfinite(y_value):
                raise ValueError
        except (TypeError, ValueError):
            invalid_numeric_rows.append(row_number)
            continue
        group_value = "All observations"
        if group_col:
            group_value = str(row.get(str(group_col), "")).strip()
            if not group_value:
                missing_group_rows.append(row_number)
                continue
        valid_points.append((x_value, y_value, group_value))

    if invalid_numeric_rows:
        shown = ", ".join(str(value) for value in invalid_numeric_rows[:10])
        suffix = " ..." if len(invalid_numeric_rows) > 10 else ""
        errors.append(f"scatter x/y 字段存在缺失或非数值: CSV 行 {shown}{suffix}")
    if missing_group_rows:
        shown = ", ".join(str(value) for value in missing_group_rows[:10])
        suffix = " ..." if len(missing_group_rows) > 10 else ""
        errors.append(f"scatter group 字段存在缺失值: CSV 行 {shown}{suffix}")
    if len(valid_points) < 2:
        errors.append("scatter 至少需要 2 个有效样本")

    trend_enabled = bool((params or {}).get("trendLine"))
    if trend_enabled and valid_points:
        if str((params or {}).get("trendLineScope") or "overall") == "by_group" and group_col:
            grouped: dict[str, list[tuple[float, float, str]]] = {}
            for point in valid_points:
                grouped.setdefault(point[2], []).append(point)
            weak_groups = [
                group
                for group, points in grouped.items()
                if len(points) < 2 or len({point[0] for point in points}) < 2
            ]
            if weak_groups:
                errors.append(f"scatter 分组趋势线至少需要每组 2 个样本且 X 值不能全相同: {', '.join(weak_groups)}")
        elif len({point[0] for point in valid_points}) < 2:
            errors.append("scatter 趋势线至少需要 2 个不同的 X 值")
    return errors


async def handle_figure_templates(request: WsRequest, *, identity: dict[str, str]) -> Response:
    if identity.get("role") != "researcher":
        return http_error(403, "Only researchers can access Figure Studio")
    templates = [{**item, "previewUrl": f"/api/researcher/figure-templates/{item['id']}/preview"} for item in FIGURE_TEMPLATES]
    return http_json_response({"ok": True, "data": templates})


async def handle_figure_template_preview(request: WsRequest, template_id: str, *, identity: dict[str, str]) -> Response:
    if identity.get("role") != "researcher":
        return http_error(403, "Only researchers can access Figure Studio")
    relative = TEMPLATE_PREVIEWS.get(template_id)
    if not relative:
        return http_error(404, "模板预览图不存在")
    path = (_figure_assets_root() / relative).resolve()
    if not path.is_file() or _figure_assets_root().resolve() not in path.parents:
        return http_error(404, "模板预览图不存在")
    return http_response(path.read_bytes(), content_type="image/png", extra_headers=[("Cache-Control", "public, max-age=3600")])


async def handle_create_figure_job(request: WsRequest, storage, *, identity: dict[str, str]) -> Response:
    if identity.get("role") != "researcher":
        return http_error(403, "Only researchers can create figure jobs")
    body = await _body(request)
    if isinstance(body, Response):
        return body
    job = await storage.create_research_job({
        "user_id": identity.get("user_id", ""), "user_role": "researcher", "job_type": "figure_preview",
        "status": "draft", "payload": {"name": str(body.get("name") or "Untitled figure"), "backend": "python"},
        "max_attempts": 2,
    })
    return http_json_response({"ok": True, "data": job}, status=201)


async def handle_upload_figure_data(request: WsRequest, storage, job_id: str, *, identity: dict[str, str]) -> Response:
    body = await _body(request)
    if isinstance(body, Response):
        return body
    job = await storage.get_research_job(int(job_id), identity.get("user_id", ""), "researcher")
    if not job or job.get("jobType") != "figure_preview":
        return http_error(404, "Figure job not found")
    filename = Path(str(body.get("fileName") or "data.csv")).name
    if filename.lower().split(".")[-1] != "csv":
        return http_error(415, "第一阶段仅支持 CSV 文件")
    try:
        raw = _decode(str(body.get("fileData") or ""))
        schema = _inspect_csv(raw)
    except Exception as exc:
        return http_error(400, f"CSV 解析失败: {exc}")
    if len(raw) > 50 * 1024 * 1024:
        return http_error(413, "File exceeds the 50 MB limit")
    user_dir = Path(".nanobot") / "figure-jobs" / identity.get("user_id", "")
    user_dir.mkdir(parents=True, exist_ok=True)
    path = user_dir / f"{uuid.uuid4().hex}_{filename}"
    path.write_bytes(raw)
    payload = {**job.get("payload", {}), "filePath": str(path), "fileName": filename, "schema": schema}
    await storage.update_research_job(int(job_id), {"status": "data_uploaded", "progress": 10, "payload": payload})
    return http_json_response({"ok": True, "data": {"jobId": int(job_id), "fileName": filename, "schema": schema}})


async def handle_set_figure_template(request: WsRequest, storage, job_id: str, *, identity: dict[str, str]) -> Response:
    body = await _body(request)
    if isinstance(body, Response):
        return body
    job = await storage.get_research_job(int(job_id), identity.get("user_id", ""), "researcher")
    template = next((item for item in FIGURE_TEMPLATES if item["id"] == body.get("templateId")), None)
    if not job or not template:
        return http_error(404, "Figure job or template not found")
    mapping = body.get("mapping") if isinstance(body.get("mapping"), dict) else {}
    stored_mapping = job.get("payload", {}).get("mapping", {})
    if not set(template["required"]).issubset(mapping):
        mapping = stored_mapping or mapping
    params = body.get("params") if isinstance(body.get("params"), dict) else {}
    schema = job.get("payload", {}).get("schema", {})
    errors = _mapping_errors(template, mapping, schema, params)
    if template["id"] == "scatter" and not errors:
        errors.extend(_validate_scatter_csv(job.get("payload", {}).get("filePath", ""), mapping, params))
    prompt = str(body.get("prompt") or body.get("conclusion") or "").strip()
    if not template["required"] and not prompt:
        errors.append("请填写图形内容描述")
    payload = {**job.get("payload", {}), "templateId": template["id"], "mapping": mapping, "params": params, "prompt": prompt, "validation": {"errors": errors}}
    status = "ready_to_preview" if not errors else "template_pending"
    await storage.update_research_job(int(job_id), {"status": status, "progress": 25 if not errors else 15, "payload": payload})
    return http_json_response({"ok": True, "data": {"valid": not errors, "errors": errors, "template": template}})


async def handle_normalize_figure_data(request: WsRequest, storage, job_id: str, *, identity: dict[str, str]) -> Response:
    body = await _body(request)
    if isinstance(body, Response):
        return body
    job = await storage.get_research_job(int(job_id), identity.get("user_id", ""), "researcher")
    template_id = str(body.get("templateId") or "grouped_bar")
    if not job:
        return http_error(404, "Figure job not found")
    mapping = _recommend_mapping(job.get("payload", {}).get("schema", {}), template_id)
    schema = job.get("payload", {}).get("schema", {})
    template = next((x for x in FIGURE_TEMPLATES if x["id"] == template_id), None)
    if not template:
        return http_error(404, "图表模板不存在")
    errors = _mapping_errors(template, mapping, schema)
    if template["id"] == "scatter" and not errors:
        errors.extend(_validate_scatter_csv(job.get("payload", {}).get("filePath", ""), mapping, {}))
    payload = {**job.get("payload", {}), "templateId": template_id, "mapping": mapping, "validation": {"errors": errors, "source": "ai-normalizer"}}
    await storage.update_research_job(int(job_id), {"status": "ready_to_preview" if not errors else "template_pending", "progress": 25 if not errors else 15, "payload": payload})
    return http_json_response({"ok": True, "data": {"mapping": mapping, "valid": not errors, "errors": errors, "reason": "根据列名语义和数据类型自动匹配"}})


async def handle_run_figure_preview(request: WsRequest, storage, job_id: str, *, identity: dict[str, str]) -> Response:
    job = await storage.get_research_job(int(job_id), identity.get("user_id", ""), "researcher")
    if not job:
        return http_error(404, "Figure job not found")
    errors = job.get("payload", {}).get("validation", {}).get("errors", [])
    if errors:
        return http_error(400, "请先修正字段映射: " + ", ".join(errors))
    await storage.update_research_job(int(job_id), {"status": "queued", "progress": 0})
    from nanobot.services.research_jobs import ensure_research_job_worker
    ensure_research_job_worker(storage)
    return http_json_response({"ok": True, "data": await storage.get_research_job(int(job_id), identity.get("user_id", ""), "researcher")}, status=202)


async def handle_get_figure_job(request: WsRequest, storage, job_id: str, *, identity: dict[str, str]) -> Response:
    job = await storage.get_research_job(int(job_id), identity.get("user_id", ""), "researcher")
    if not job or job.get("jobType") != "figure_preview":
        return http_error(404, "Figure job not found")
    return http_json_response({"ok": True, "data": job})
