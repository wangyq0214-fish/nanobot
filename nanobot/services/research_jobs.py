"""Small PostgreSQL-backed worker for researcher jobs."""

from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger

from nanobot.storage.storage_wrapper import StorageWrapper

_worker_tasks: set[asyncio.Task[Any]] = set()


def ensure_research_job_worker(storage: StorageWrapper) -> None:
    """Start one worker for this event loop and recover interrupted jobs."""
    loop = asyncio.get_running_loop()
    if any(not task.done() for task in _worker_tasks):
        return
    task = loop.create_task(_worker_loop(storage))
    _worker_tasks.add(task)
    task.add_done_callback(_worker_tasks.discard)


async def _worker_loop(storage: StorageWrapper) -> None:
    await storage.recover_research_jobs()
    while True:
        try:
            job = await storage.claim_research_job()
            if not job:
                await asyncio.sleep(1)
                continue
            try:
                if job["jobType"] == "attachment_parse":
                    await _parse_attachment_job(storage, job)
                elif job["jobType"] == "artifact_generate":
                    await _generate_artifact_job(storage, job)
                elif job["jobType"] == "figure_preview":
                    await _generate_figure_preview_job(storage, job)
                else:
                    raise RuntimeError(f"Unsupported research job type: {job['jobType']}")
                await storage.update_research_job(job["id"], {
                    "status": "succeeded", "progress": 100, "finished_at": datetime.utcnow(),
                })
            except Exception as exc:
                logger.exception("Research job {} failed", job.get("id"))
                failed = job.get("attempts", 1) >= job.get("maxAttempts", 3)
                if job.get("jobType") == "attachment_parse":
                    attachment_id = (job.get("payload") or {}).get("attachmentId")
                    if attachment_id:
                        await storage.update_research_attachment(int(attachment_id), {
                            "parse_status": "failed" if failed else "queued",
                            "summary": str(exc),
                        })
                await storage.update_research_job(job["id"], {
                    "status": "failed" if failed else "queued",
                    "error_message": str(exc),
                    "finished_at": datetime.utcnow() if failed else None,
                })
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Research job worker loop failed")
            await asyncio.sleep(1)


async def _parse_attachment_job(storage: StorageWrapper, job: dict[str, Any]) -> None:
    from nanobot.api.handlers.research_workspace import _parse_attachment

    payload = job.get("payload", {})
    attachment_id = int(payload["attachmentId"])
    attachment = await storage.get_research_attachment(attachment_id)
    if not attachment:
        raise RuntimeError("Attachment no longer exists")
    await storage.update_research_attachment(attachment_id, {"parse_status": "running"})
    parsed = _parse_attachment(Path(payload["filePath"]), str(payload.get("fileType", "txt")))
    if parsed["chunks"]:
        await storage.create_research_attachment_chunks(attachment_id, parsed["chunks"])
    await storage.update_research_attachment(attachment_id, {
        "parse_status": "ready", "summary": parsed["summary"], "metadata": parsed.get("metadata", {}),
    })


async def _generate_artifact_job(storage: StorageWrapper, job: dict[str, Any]) -> None:
    from nanobot.api.artifact_generators import generate_artifact
    from nanobot.api.handlers.research_artifacts import _load_sources

    payload = job.get("payload", {})
    artifact_id = int(payload["artifactId"])
    artifact = await storage.get_research_artifact(artifact_id)
    if not artifact:
        raise RuntimeError("Artifact no longer exists")
    sources = await _load_sources(storage, job["userId"], payload.get("sourceRefs", []))
    content, metadata = await generate_artifact(artifact["type"], artifact["title"], sources, payload.get("config", {}))
    old = artifact.get("metadata") if isinstance(artifact.get("metadata"), dict) else {}
    await storage.update_research_artifact(artifact_id, {
        "status": "ready", "content": content, "metadata": {**old, **metadata}, "error_message": "",
    })


async def _generate_figure_preview_job(storage: StorageWrapper, job: dict[str, Any]) -> None:
    """Render a small PNG preview from a validated CSV mapping."""
    import base64
    import csv
    import io
    import math

    payload = job.get("payload", {})
    template = payload.get("templateId")
    mapping = payload.get("mapping", {})
    params = payload.get("params", {})
    if template in {"mechanism_schematic", "graphical_abstract"}:
        if not os.environ.get("OPENROUTER_API_KEY"):
            raise RuntimeError("生成概念图需要配置 OPENROUTER_API_KEY")
        prompt = str(payload.get("prompt") or "").strip()
        if not prompt:
            raise RuntimeError("请填写图形内容描述")
        root = Path(__file__).resolve().parents[2]
        script = root / ".nanobot" / "templates" / "researcher" / "skills" / "nature-figure" / "scripts" / "generate_openrouter_schematic.py"
        outdir = root / ".nanobot" / "figure-jobs" / str(job["userId"]) / f"concept_{job['id']}"
        outdir.mkdir(parents=True, exist_ok=True)
        aspect = "4:3" if template == "mechanism_schematic" else "16:9"
        process = await asyncio.create_subprocess_exec(sys.executable, str(script), "--prompt", prompt, "--raw", "--outdir", str(outdir), "--basename", "figure", "--aspect-ratio", aspect, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await process.communicate()
        if process.returncode:
            raise RuntimeError(stderr.decode("utf-8", errors="replace").strip() or "概念图生成失败")
        output = next((path for path in outdir.glob("figure.*") if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}), None)
        if not output:
            raise RuntimeError("图片服务未返回有效图片")
        mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}.get(output.suffix.lower(), "image/png")
        encoded = base64.b64encode(output.read_bytes()).decode("ascii")
        await storage.update_research_job(job["id"], {"result": {"template": template, "previewMime": mime, "previewData": f"data:{mime};base64,{encoded}", "outputPath": str(output), "logs": [stdout.decode("utf-8", errors="replace")]}, "progress": 100})
        return
    path = Path(payload["filePath"])
    if not path.is_file():
        raise RuntimeError("Figure input data no longer exists")
    supported_templates = {"volcano", "roc", "dotplot", "marginal", "paired", "grouped_bar", "boxplot", "scatter", "line", "heatmap", "forest", "multi_panel"}
    if template not in supported_templates:
        raise RuntimeError(f"不支持的图表模板: {template}")
    native_templates = {"volcano", "roc", "dotplot", "marginal", "paired", "grouped_bar", "line", "heatmap"}
    if template in native_templates:
        root = Path(__file__).resolve().parents[2]
        prefix = path.with_name(f"native_{template}_{job['id']}")
        if template == "line":
            script = root / ".nanobot" / "templates" / "researcher" / "skills" / "nature-figure" / "assets" / "figures4papers" / "figure_ophthal_review" / "plot_trend.py"
            command = [sys.executable, str(script), "--input", str(path), "--output", str(prefix), "--x-col", mapping["x"], "--value-col", mapping["y"], "--group-col", mapping["group"]]
            if mapping.get("event"):
                command += ["--event-col", mapping["event"]]
            else:
                command.append("--hide-events")
            if params.get("cumulative", False):
                command.append("--cumulative")
            if not params.get("showMarkers", True):
                command.append("--hide-markers")
            if not params.get("showEvents", True):
                command.append("--hide-events")
            if params.get("showFill", False):
                command.append("--show-fill")
        elif template == "heatmap":
            script = root / ".nanobot" / "templates" / "researcher" / "skills" / "nature-figure" / "assets" / "figures4papers" / "figure_ophthal_review" / "plot_composition.py"
            command = [sys.executable, str(script), "--input", str(path), "--output", str(prefix), "--row-col", mapping["row"], "--column-col", mapping["column"], "--value-col", mapping["value"], "--color-map", str(params.get("colorMap", "Reds"))]
            if params.get("colorMin") not in (None, ""):
                command += ["--vmin", str(params["colorMin"])]
            if params.get("colorMax") not in (None, ""):
                command += ["--vmax", str(params["colorMax"])]
            if not params.get("showCellValues", True):
                command.append("--hide-values")
            if not params.get("showColorbar", True):
                command.append("--hide-colorbar")
        else:
            script = root / ".nanobot" / "templates" / "researcher" / "skills" / "nature-figure" / "scripts" / "plot_templates.py"
            command = [sys.executable, str(script), template, "--input", str(path), "--output", str(prefix)]
        if template == "volcano":
            command += ["--gene-col", mapping["gene"], "--effect-col", mapping["effect"], "--p-col", mapping["pvalue"], "--effect-threshold", str(params.get("effectThreshold", 1)), "--p-threshold", str(params.get("pThreshold", .05)), "--top-labels", str(params.get("topLabels", 10))]
        elif template == "roc":
            tpr_columns = mapping["tpr"] if isinstance(mapping["tpr"], list) else [mapping["tpr"]]
            command += ["--fpr-col", mapping["fpr"], "--tpr-cols", ",".join(tpr_columns)]
            if not params.get("showBaseline", True): command.append("--hide-baseline")
        elif template == "dotplot":
            command += ["--row-col", mapping["row"], "--column-col", mapping["column"], "--size-col", mapping["size"], "--color-col", mapping["color"], "--color-map", str(params.get("colorMap", "viridis"))]
        elif template == "marginal":
            command += ["--x-col", mapping["x"], "--y-col", mapping["y"], "--bins", str(params.get("bins", 24))]
            if mapping.get("group"): command += ["--group-col", mapping["group"]]
            else: command += ["--group-col", ""]
        elif template == "paired":
            command += ["--id-col", mapping["subject"], "--condition-col", mapping["condition"], "--value-col", mapping["value"]]
            if not params.get("showPoints", True): command.append("--hide-points")
        elif template == "grouped_bar":
            command += ["--category-col", mapping["category"], "--group-col", mapping["group"], "--value-col", mapping["value"], "--error-type", str(params.get("errorBar", "SEM"))]
            if mapping.get("error"):
                command += ["--error-col", mapping["error"]]
        process = await asyncio.create_subprocess_exec(*command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await process.communicate()
        if process.returncode:
            raise RuntimeError(stderr.decode("utf-8", errors="replace").strip() or "skill 模板执行失败")
        bundle = json.loads(stdout.decode("utf-8"))
        preview_path = Path(bundle["outputs"].get("png", prefix.with_suffix(".png")))
        if not preview_path.exists():
            try:
                from PIL import Image
                preview_path = prefix.with_suffix(".png")
                with Image.open(bundle["outputs"]["tiff"]) as image:
                    image.thumbnail((1800, 1400))
                    image.convert("RGB").save(preview_path, "PNG", optimize=True)
            except ImportError as exc:
                raise RuntimeError("生成模板预览需要 Pillow") from exc
        encoded = base64.b64encode(preview_path.read_bytes()).decode("ascii")
        qa = json.loads(Path(bundle["qa"]).read_text(encoding="utf-8"))
        renderer = "nature-figure/plot_trend.py" if template == "line" else "nature-figure/plot_composition.py" if template == "heatmap" else "nature-figure/plot_templates.py"
        result = {"template": template, "renderer": renderer, "previewMime": "image/png", "previewData": f"data:image/png;base64,{encoded}", "outputPath": str(preview_path), "outputs": bundle["outputs"], "qaPath": bundle["qa"], "qa": qa, "logs": ["nature-figure 原生模板执行完成"]}
        await storage.update_research_job(job["id"], {"result": result, "progress": 100})
        return
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
        from matplotlib import font_manager
    except ImportError as exc:
        raise RuntimeError("Python preview requires matplotlib") from exc

    available_fonts = {font.name for font in font_manager.fontManager.ttflist}
    chinese_font = next((name for name in ("Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "Source Han Sans CN") if name in available_fonts), "DejaVu Sans")
    plt.rcParams.update({"font.sans-serif": [chinese_font, "DejaVu Sans"], "axes.unicode_minus": False})

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    fig, ax = plt.subplots(figsize=(7.2, 4.6), dpi=120)
    if template == "volcano":
        xs = [float(row[mapping["effect"]]) for row in rows]
        ys = [-math.log10(max(float(row[mapping["pvalue"]]), 1e-12)) for row in rows]
        effect_threshold = float(params.get("effectThreshold", 1))
        p_threshold = float(params.get("pThreshold", .05))
        colors = ["#b2182b" if x >= effect_threshold and p < p_threshold else "#2166ac" if x <= -effect_threshold and p < p_threshold else "#b8b8b8" for x, p in zip(xs, (float(row[mapping["pvalue"]]) for row in rows))]
        ax.scatter(xs, ys, s=24, c=colors, alpha=.75, edgecolors="none")
        ax.axvline(-effect_threshold, ls="--", lw=.7, color="#777"); ax.axvline(effect_threshold, ls="--", lw=.7, color="#777"); ax.axhline(-math.log10(p_threshold), ls="--", lw=.7, color="#777")
        label_count = max(0, int(params.get("topLabels", 10)))
        for index in sorted(range(len(rows)), key=lambda i: ys[i], reverse=True)[:label_count]:
            ax.annotate(str(rows[index][mapping["gene"]]), (xs[index], ys[index]), fontsize=7, xytext=(3, 3), textcoords="offset points")
        ax.set_xlabel("效应大小"); ax.set_ylabel("-log10(校正 P 值)")
    elif template == "roc":
        fpr = np.asarray([float(row[mapping["fpr"]]) for row in rows]); order = np.argsort(fpr)
        tpr_columns = mapping["tpr"] if isinstance(mapping["tpr"], list) else [mapping["tpr"]]
        for column in tpr_columns:
            tpr = np.asarray([float(row[column]) for row in rows])[order]; auc = np.trapezoid(tpr, fpr[order])
            ax.plot(fpr[order], tpr, lw=1.6, label=f"{column} (AUC={auc:.3f})")
        if params.get("showBaseline", True): ax.plot([0, 1], [0, 1], "--", color="#999", label="随机基线")
        ax.set_xlabel("假阳性率"); ax.set_ylabel("真阳性率"); ax.legend(frameon=False)
    elif template == "dotplot":
        xcats = list(dict.fromkeys(row[mapping["column"]] for row in rows))
        ycats = list(dict.fromkeys(row[mapping["row"]] for row in rows))
        sizes = np.asarray([max(0, float(row[mapping["size"]])) for row in rows]); size_max = max(float(sizes.max()), 1)
        colors = np.asarray([float(row[mapping["color"]]) for row in rows])
        scatter = ax.scatter([xcats.index(row[mapping["column"]]) for row in rows], [ycats.index(row[mapping["row"]]) for row in rows], s=15 + 180 * np.sqrt(sizes / size_max), c=colors, cmap=params.get("colorMap", "viridis"), edgecolors="#666", linewidths=.3)
        fig.colorbar(scatter, ax=ax, label=mapping["color"])
        ax.set_xticks(range(len(xcats)), xcats); ax.set_yticks(range(len(ycats)), ycats)
    elif template == "marginal":
        fig.clear(); grid = fig.add_gridspec(4, 4, hspace=.05, wspace=.05); ax = fig.add_subplot(grid[1:, :3]); top = fig.add_subplot(grid[0, :3], sharex=ax); right = fig.add_subplot(grid[1:, 3], sharey=ax)
        group_col = mapping.get("group"); groups = list(dict.fromkeys(row[group_col] for row in rows)) if group_col else ["全部数据"]
        for group in groups:
            subset = [row for row in rows if not group_col or row[group_col] == group]; xs = [float(row[mapping["x"]]) for row in subset]; ys = [float(row[mapping["y"]]) for row in subset]
            ax.scatter(xs, ys, s=18, alpha=.55, label=group); top.hist(xs, bins=max(2, int(params.get("bins", 24))), histtype="step"); right.hist(ys, bins=max(2, int(params.get("bins", 24))), orientation="horizontal", histtype="step")
        ax.legend(frameon=False); ax.set_xlabel(mapping["x"]); ax.set_ylabel(mapping["y"]); top.tick_params(labelbottom=False); right.tick_params(labelleft=False)
    elif template == "paired":
        conditions = list(dict.fromkeys(row[mapping["condition"]] for row in rows))
        subjects = list(dict.fromkeys(row[mapping["subject"]] for row in rows))
        for subject in subjects:
            values = [float(next(row[mapping["value"]] for row in rows if row[mapping["subject"]] == subject and row[mapping["condition"]] == condition)) for condition in conditions]
            ax.plot(range(len(conditions)), values, marker="o" if params.get("showPoints", True) else None, color="#666666", alpha=.75)
        ax.set_xticks(range(len(conditions)), conditions); ax.set_ylabel(mapping["value"])
    elif template == "line":
        for group in dict.fromkeys(row[mapping["group"]] for row in rows):
            subset = sorted((row for row in rows if row[mapping["group"]] == group), key=lambda row: float(row[mapping["x"]]))
            ax.plot([float(row[mapping["x"]]) for row in subset], [float(row[mapping["y"]]) for row in subset], marker="o" if params.get("showMarkers", True) else None, label=group)
        ax.legend(frameon=False); ax.set_xlabel(mapping["x"]); ax.set_ylabel(mapping["y"])
    elif template == "heatmap":
        xcats = list(dict.fromkeys(row[mapping["column"]] for row in rows)); ycats = list(dict.fromkeys(row[mapping["row"]] for row in rows))
        matrix = [[float(next(row[mapping["value"]] for row in rows if row[mapping["row"]] == y and row[mapping["column"]] == x)) for x in xcats] for y in ycats]
        image = ax.imshow(matrix, cmap=params.get("colorMap", "viridis"), aspect="auto"); fig.colorbar(image, ax=ax, label=mapping["value"]); ax.set_xticks(range(len(xcats)), xcats); ax.set_yticks(range(len(ycats)), ycats)
    elif template == "forest":
        labels = [row[mapping["label"]] for row in rows]; effects = [float(row[mapping["effect"]]) for row in rows]; lower = [effects[i] - float(row[mapping["lower"]]) for i, row in enumerate(rows)]; upper = [float(row[mapping["upper"]]) - effects[i] for i, row in enumerate(rows)]
        ax.errorbar(effects, range(len(labels)), xerr=[lower, upper], fmt="o", color="#2166AC"); ax.set_yticks(range(len(labels)), labels); ax.axvline(float(params.get("reference", 1)), ls="--", color="#999")
    elif template == "multi_panel":
        panels = list(dict.fromkeys(row[mapping["panel"]] for row in rows)); panel_columns = max(1, min(int(params.get("columns", 2)), len(panels))); panel_rows = math.ceil(len(panels) / panel_columns)
        fig.clear(); axes = np.asarray(fig.subplots(panel_rows, panel_columns, squeeze=False)).ravel()
        for panel_ax, panel in zip(axes, panels):
            subset = [row for row in rows if row[mapping["panel"]] == panel]; categories = list(dict.fromkeys(row[mapping["category"]] for row in subset)); means = [np.mean([float(row[mapping["value"]]) for row in subset if row[mapping["category"]] == category]) for category in categories]
            panel_ax.bar(categories, means, color="#2166AC"); panel_ax.set_title(str(panel)); panel_ax.tick_params(axis="x", rotation=25); panel_ax.spines["top"].set_visible(False); panel_ax.spines["right"].set_visible(False)
        for panel_ax in axes[len(panels):]: panel_ax.set_visible(False)
    elif template == "scatter":
        x_col = mapping["x"]
        y_col = mapping["y"]
        group_col = mapping.get("group") or None
        if not rows:
            raise RuntimeError("scatter 至少需要 2 个有效样本")
        required_columns = [x_col, y_col] + ([group_col] if group_col else [])
        missing_columns = [column for column in required_columns if column not in rows[0]]
        if missing_columns:
            raise RuntimeError("scatter CSV 缺少字段: " + ", ".join(str(column) for column in missing_columns))

        invalid_rows: list[int] = []
        missing_group_rows: list[int] = []
        points: list[dict[str, Any]] = []
        for row_number, row in enumerate(rows, start=2):
            try:
                x_value = float(str(row.get(x_col, "")).strip())
                y_value = float(str(row.get(y_col, "")).strip())
                if not math.isfinite(x_value) or not math.isfinite(y_value):
                    raise ValueError
            except (TypeError, ValueError):
                invalid_rows.append(row_number)
                continue
            group_value = "All observations"
            if group_col:
                group_value = str(row.get(group_col, "")).strip()
                if not group_value:
                    missing_group_rows.append(row_number)
                    continue
            points.append({"x": x_value, "y": y_value, "group": group_value})
        if invalid_rows:
            shown = ", ".join(str(value) for value in invalid_rows[:10])
            suffix = " ..." if len(invalid_rows) > 10 else ""
            raise RuntimeError(f"scatter x/y 字段存在缺失或非数值: CSV 行 {shown}{suffix}")
        if missing_group_rows:
            shown = ", ".join(str(value) for value in missing_group_rows[:10])
            suffix = " ..." if len(missing_group_rows) > 10 else ""
            raise RuntimeError(f"scatter group 字段存在缺失值: CSV 行 {shown}{suffix}")
        if len(points) < 2:
            raise RuntimeError("scatter 至少需要 2 个有效样本")

        palette = ["#2166AC", "#B2182B", "#762A83", "#F1A340", "#666666", "#92C5DE"]
        groups = list(dict.fromkeys(point["group"] for point in points))
        group_counts: dict[str, int] = {}
        trend_enabled = bool(params.get("trendLine"))
        trend_scope = str(params.get("trendLineScope") or "overall")
        trend_scope = "by_group" if trend_scope == "by_group" and group_col else "overall"
        trends: list[dict[str, Any]] = []
        ax.clear()
        fig.set_size_inches(183 / 25.4, 120 / 25.4)
        for index, group in enumerate(groups):
            subset = [point for point in points if point["group"] == group]
            xs = np.asarray([point["x"] for point in subset], dtype=float)
            ys = np.asarray([point["y"] for point in subset], dtype=float)
            group_counts[group] = int(len(subset))
            color = palette[index % len(palette)]
            ax.scatter(xs, ys, s=18, alpha=0.72, color=color, edgecolors="white", linewidths=0.35, label=f"{group} (n={len(subset)})" if group_col else None, rasterized=len(points) > 50000)

        def add_trend_line(xs: Any, ys: Any, label: str | None, color: str) -> None:
            if len(xs) < 2 or len(set(float(value) for value in xs)) < 2:
                raise RuntimeError("scatter 趋势线至少需要 2 个样本且 X 值不能全相同" + (f": {label}" if label else ""))
            slope, intercept = np.polyfit(xs, ys, 1)
            fitted = slope * xs + intercept
            ss_res = float(np.sum((ys - fitted) ** 2))
            ss_tot = float(np.sum((ys - np.mean(ys)) ** 2))
            r_squared = 1.0 if ss_tot == 0 else 1.0 - ss_res / ss_tot
            line_x = np.linspace(float(np.min(xs)), float(np.max(xs)), 100)
            ax.plot(line_x, slope * line_x + intercept, color=color, linewidth=1.05, linestyle="-", label=("Linear trend" if label is None else f"{label} trend"))
            trends.append({"group": label, "n": int(len(xs)), "slope": float(slope), "intercept": float(intercept), "r_squared": float(r_squared)})

        if trend_enabled:
            if trend_scope == "by_group":
                for index, group in enumerate(groups):
                    subset = [point for point in points if point["group"] == group]
                    add_trend_line(
                        np.asarray([point["x"] for point in subset], dtype=float),
                        np.asarray([point["y"] for point in subset], dtype=float),
                        group,
                        palette[index % len(palette)],
                    )
            else:
                add_trend_line(
                    np.asarray([point["x"] for point in points], dtype=float),
                    np.asarray([point["y"] for point in points], dtype=float),
                    None,
                    "#222222",
                )
        if group_col or trend_enabled:
            ax.legend(frameon=False, loc="best")
        ax.set_xlabel(str(params.get("xLabel") or x_col))
        ax.set_ylabel(str(params.get("yLabel") or y_col))
        if params.get("title"):
            ax.set_title(str(params["title"]))
        ax.grid(color="#E6E6E6", linewidth=0.35)
        ax.set_axisbelow(True)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        fig.tight_layout()

        prefix = path.with_name(f"native_scatter_{job['id']}")
        outputs = {
            "png": str(prefix.with_suffix(".png")),
            "svg": str(prefix.with_suffix(".svg")),
            "pdf": str(prefix.with_suffix(".pdf")),
            "tiff": str(prefix.with_suffix(".tiff")),
        }
        fig.savefig(outputs["png"], dpi=180, bbox_inches="tight", facecolor="white")
        fig.savefig(outputs["svg"], bbox_inches="tight", facecolor="white")
        fig.savefig(outputs["pdf"], bbox_inches="tight", facecolor="white")
        fig.savefig(outputs["tiff"], dpi=600, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        qa = {
            "template": "scatter",
            "backend": "python",
            "input": path.name,
            "output_prefix": prefix.name,
            "rows_input": len(rows),
            "rows_plotted": len(points),
            "excluded_rows": 0,
            "mapping": {"x": x_col, "y": y_col, "group": group_col},
            "parameters": {
                "trend_line": trend_enabled,
                "trend_line_scope": trend_scope,
                "group_order": groups,
                "group_counts": group_counts,
                "palette": palette,
                "trends": trends,
                "tiff_dpi": 600,
            },
            "validation": {
                "numeric_fields": [x_col, y_col],
                "missing_required_values": "fail",
                "minimum_effective_samples": 2,
                "trend_line_method": "ordinary least squares via numpy.polyfit",
            },
        }
        qa_path = prefix.with_suffix(".qa.json")
        qa_path.write_text(json.dumps(qa, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        encoded = base64.b64encode(Path(outputs["png"]).read_bytes()).decode("ascii")
        result = {"template": template, "renderer": "python/scatter", "previewMime": "image/png", "previewData": f"data:image/png;base64,{encoded}", "outputPath": outputs["png"], "outputs": outputs, "qaPath": str(qa_path), "qa": qa, "logs": ["Python scatter template exported PNG/SVG/PDF/600 dpi TIFF/QA"]}
        await storage.update_research_job(job["id"], {"result": result, "progress": 100})
        return
    else:
        category = mapping["category"]
        value = mapping["value"]
        groups = mapping.get("group")
        categories = list(dict.fromkeys(row[category] for row in rows))
        if template == "boxplot":
            ax.boxplot([[float(row[value]) for row in rows if row[category] == item] for item in categories], tick_labels=categories, patch_artist=True, boxprops={"facecolor": "#D9EAF7"})
            if params.get("showPoints", True):
                for index, item in enumerate(categories, start=1):
                    values = [float(row[value]) for row in rows if row[category] == item]
                    jitter = np.linspace(-.06, .06, len(values)) if values else []
                    ax.scatter(index + jitter, values, s=12, alpha=.55, color="#2166AC", edgecolors="white", linewidth=.3)
        else:
            group_values = list(dict.fromkeys(row[groups] for row in rows)) if groups else ["All"]
            width = .72 / max(1, len(group_values))
            for index, group in enumerate(group_values):
                means = []
                errors = []
                for item in categories:
                    values = [float(row[value]) for row in rows if row[category] == item and (not groups or row[groups] == group)]
                    means.append(sum(values) / len(values) if values else 0)
                    error_mode = params.get("errorBar", "标准误（SEM）")
                    if error_mode == "不显示" or len(values) < 2:
                        errors.append(0)
                    else:
                        sd = float(np.std(values, ddof=1))
                        sem = sd / math.sqrt(len(values))
                        errors.append(sd if "SD" in error_mode else 1.96 * sem if "95%" in error_mode else sem)
                positions = [i + (index - (len(group_values) - 1) / 2) * width for i in range(len(categories))]
                ax.bar(positions, means, yerr=errors if any(errors) else None, capsize=3, width=width, label=group, color=["#2166AC", "#B2182B", "#1B7837"][index % 3])
            if groups:
                ax.legend(frameon=False)
            ax.set_xticks(range(len(categories)), categories)
        ax.set_xlabel(category); ax.set_ylabel(value)
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    output = path.with_name(f"preview_{job['id']}.png")
    fig.tight_layout(); fig.savefig(output, bbox_inches="tight", facecolor="white"); plt.close(fig)
    encoded = base64.b64encode(output.read_bytes()).decode("ascii")
    result = {"template": template, "previewMime": "image/png", "previewData": f"data:image/png;base64,{encoded}", "outputPath": str(output), "logs": ["Python matplotlib preview generated"]}
    await storage.update_research_job(job["id"], {"result": result, "progress": 100})
