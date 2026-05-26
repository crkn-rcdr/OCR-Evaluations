#!/usr/bin/env python3
"""Generate Plotly dashboards for the OCR evaluation workbooks.

Default usage:

  python tools/generate_ocr_plots.py

This reads:

- test-results/paddle_vs_abbyy_errors_artifacts.xlsx
- test-results/first_article_ocr_comparison.xlsx

and writes an HTML dashboard to:

- test-results/plots/ocr_evaluation_dashboard.html

It also writes PNG files for README embedding under:

- test-results/plots/png/
"""

from __future__ import annotations

import argparse
import html
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from openpyxl import load_workbook
from plotly import graph_objects as go
from plotly.io import to_html, write_image
from plotly.subplots import make_subplots


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PADDLE_VS_ABBYY = REPO_ROOT / "test-results" / "paddle_vs_abbyy_errors_artifacts.xlsx"
DEFAULT_FIRST_ARTICLE = REPO_ROOT / "test-results" / "first_article_ocr_comparison.xlsx"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "test-results" / "plots"
DEFAULT_OUTPUT_HTML = DEFAULT_OUTPUT_DIR / "ocr_evaluation_dashboard.html"
DEFAULT_OUTPUT_PNG_DIR = DEFAULT_OUTPUT_DIR / "png"


@dataclass(frozen=True)
class SheetSummary:
    label: str
    paddle_source: str
    abbyy_source: str
    paddle_line_count: int
    abbyy_line_count: int
    paddle_word_count: int
    abbyy_word_count: int
    paddle_artifact_entries: int
    abbyy_artifact_entries: int
    paddle_error_counts: dict[str, int]
    abbyy_error_counts: dict[str, int]


@dataclass(frozen=True)
class HumanSummary:
    rank: int
    label: str
    source_path: str
    word_accuracy: float
    wer: float
    cer: float
    word_edits: int
    substitutions: int
    insertions: int
    deletions: int
    character_edits: int
    human_words: int
    ocr_words: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate Plotly visualizations for OCR evaluation workbooks."
    )
    parser.add_argument(
        "--paddle-vs-abbyy",
        type=Path,
        default=DEFAULT_PADDLE_VS_ABBYY,
        help="Path to paddle_vs_abbyy_errors_artifacts.xlsx",
    )
    parser.add_argument(
        "--first-article",
        type=Path,
        default=DEFAULT_FIRST_ARTICLE,
        help="Path to first_article_ocr_comparison.xlsx",
    )
    parser.add_argument(
        "--output-html",
        type=Path,
        default=DEFAULT_OUTPUT_HTML,
        help="Output HTML dashboard path.",
    )
    parser.add_argument(
        "--output-png-dir",
        type=Path,
        default=DEFAULT_OUTPUT_PNG_DIR,
        help="Output directory for PNG chart exports.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    paddle_vs_abbyy = args.paddle_vs_abbyy.resolve()
    first_article = args.first_article.resolve()
    output_html = args.output_html.resolve()
    output_png_dir = args.output_png_dir.resolve()
    output_html.parent.mkdir(parents=True, exist_ok=True)
    output_png_dir.mkdir(parents=True, exist_ok=True)

    whole_page = load_whole_page_summaries(paddle_vs_abbyy)
    human_rows = load_human_summaries(first_article)

    figures = [
        (
            "line_count_recovery",
            "Whole-Page Line Recovery",
            (
                "How many lines each workflow recovered relative to ABBYY. "
                "Values above 100% mean Paddle produced more line segments than "
                "ABBYY, which can include over-segmentation or duplicates."
            ),
            build_line_recovery_figure(whole_page),
        ),
        (
            "word_count_recovery",
            "Whole-Page Word Recovery",
            (
                "How many words each workflow recovered relative to ABBYY. "
                "This makes the preprocess-only under-extraction problem obvious "
                "and shows why `PaddleOCR (No VL)` became the base pipeline."
            ),
            build_word_recovery_figure(whole_page),
        ),
        (
            "whole_page_word_counts",
            "Whole-Page Word Counts",
            (
                "Absolute whole-page word counts for ABBYY and each Paddle-based "
                "workflow."
            ),
            build_absolute_word_count_figure(whole_page),
        ),
        (
            "artifact_totals",
            "Whole-Page Artifact Totals",
            (
                "Overall artifact-entry counts from the side-by-side workbook. "
                "Lower is cleaner, but these totals should be read together with "
                "the coverage chart above."
            ),
            build_artifact_totals_figure(whole_page),
        ),
        (
            "artifact_categories",
            "Artifact Categories vs ABBYY",
            (
                "Each subplot shows one Paddle workflow. Category values are "
                "expressed as a percent of ABBYY's count for the same category, "
                "so 100% means parity with ABBYY, above 100% means more tagged "
                "artifacts than ABBYY, and below 100% means fewer."
            ),
            build_artifact_category_vs_abbyy_figure(whole_page),
        ),
        (
            "human_tradeoffs",
            "Human-Transcription Tradeoffs",
            (
                "WER and CER plotted together for the comparison of human "
                "transcription of the first article on the page to the AI "
                "transcription. Points closer to the lower-left are better; "
                "marker size tracks word accuracy."
            ),
            build_human_scatter_figure(human_rows),
        ),
        (
            "human_edit_breakdown",
            "Human-Transcription Edit Breakdown",
            (
                "Word-level substitutions, insertions, and deletions for the "
                "comparison of human transcription of the first article on the "
                "page to the AI transcription."
            ),
            build_edit_breakdown_figure(human_rows),
        ),
    ]

    html_text = build_dashboard_html(figures, paddle_vs_abbyy, first_article)
    output_html.write_text(html_text, encoding="utf-8")
    write_png_exports(figures, output_png_dir)
    print(f"Wrote {output_html}")
    print(f"Wrote PNG charts to {output_png_dir}")


def load_whole_page_summaries(path: Path) -> list[SheetSummary]:
    workbook = load_workbook(path, data_only=True)
    summaries: list[SheetSummary] = []
    for worksheet in workbook.worksheets:
        header = [worksheet.cell(1, column).value for column in range(1, worksheet.max_column + 1)]
        error_column_map = parse_error_columns(header)
        summary_values = {
            str(worksheet.cell(row, 1).value or "").strip().lower(): worksheet.cell(row, 2).value
            for row in range(1, min(8, worksheet.max_row) + 1)
        }
        abbyy_summary_values = {
            str(worksheet.cell(row, 1).value or "").strip().lower(): worksheet.cell(row, 3).value
            for row in range(1, min(8, worksheet.max_row) + 1)
        }

        paddle_error_counts = count_nonempty_error_cells(worksheet, error_column_map, "paddle")
        abbyy_error_counts = count_nonempty_error_cells(worksheet, error_column_map, "abbyy")

        summaries.append(
            SheetSummary(
                label=friendly_whole_page_label(worksheet.title),
                paddle_source=str(summary_values.get("source file") or ""),
                abbyy_source=str(abbyy_summary_values.get("source file") or ""),
                paddle_line_count=parse_int(summary_values.get("line count")),
                abbyy_line_count=parse_int(abbyy_summary_values.get("line count")),
                paddle_word_count=parse_int(summary_values.get("word count")),
                abbyy_word_count=parse_int(abbyy_summary_values.get("word count")),
                paddle_artifact_entries=parse_int(summary_values.get("error/artifact entries")),
                abbyy_artifact_entries=parse_int(abbyy_summary_values.get("error/artifact entries")),
                paddle_error_counts=paddle_error_counts,
                abbyy_error_counts=abbyy_error_counts,
            )
        )
    return summaries


def parse_error_columns(header: list[object]) -> dict[str, dict[str, int]]:
    columns: dict[str, dict[str, int]] = {}
    for index, value in enumerate(header, start=1):
        text = str(value or "").strip()
        if " - paddle" in text:
            error_type = text.replace(" - paddle", "")
            columns.setdefault(error_type, {})["paddle"] = index
        elif " - abbyy" in text:
            error_type = text.replace(" - abbyy", "")
            columns.setdefault(error_type, {})["abbyy"] = index
    return columns


def count_nonempty_error_cells(
    worksheet,
    error_column_map: dict[str, dict[str, int]],
    side: str,
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for error_type, columns in error_column_map.items():
        column = columns.get(side)
        if column is None:
            counts[error_type] = 0
            continue
        count = 0
        for row in range(2, worksheet.max_row + 1):
            value = worksheet.cell(row, column).value
            if value is None:
                continue
            if str(value).strip():
                count += 1
        counts[error_type] = count
    return counts


def load_human_summaries(path: Path) -> list[HumanSummary]:
    workbook = load_workbook(path, data_only=True)
    worksheet = workbook["Summary"]
    rows: list[HumanSummary] = []
    for row in range(2, worksheet.max_row + 1):
        label = friendly_human_label(str(worksheet.cell(row, 2).value or ""))
        rows.append(
            HumanSummary(
                rank=parse_int(worksheet.cell(row, 1).value),
                label=label,
                source_path=str(worksheet.cell(row, 3).value or ""),
                word_accuracy=parse_float(worksheet.cell(row, 4).value),
                wer=parse_float(worksheet.cell(row, 5).value),
                cer=parse_float(worksheet.cell(row, 6).value),
                word_edits=parse_int(worksheet.cell(row, 7).value),
                substitutions=parse_int(worksheet.cell(row, 8).value),
                insertions=parse_int(worksheet.cell(row, 9).value),
                deletions=parse_int(worksheet.cell(row, 10).value),
                character_edits=parse_int(worksheet.cell(row, 11).value),
                human_words=parse_int(worksheet.cell(row, 12).value),
                ocr_words=parse_int(worksheet.cell(row, 13).value),
            )
        )
    return rows


def build_line_recovery_figure(rows: list[SheetSummary]) -> go.Figure:
    labels = [row.label for row in rows]
    line_pct = [percentage(row.paddle_line_count, row.abbyy_line_count) for row in rows]
    hover_line = [
        f"Paddle {row.paddle_line_count:,}<br>ABBYY {row.abbyy_line_count:,}"
        for row in rows
    ]

    figure = go.Figure()
    figure.add_trace(
        go.Bar(
            name="Line count vs ABBYY",
            x=labels,
            y=line_pct,
            text=[f"{value:.1f}%" for value in line_pct],
            textposition="outside",
            hovertemplate="%{x}<br>%{customdata}<extra></extra>",
            customdata=hover_line,
            marker_color="#33658A",
        )
    )
    figure.add_hline(y=100, line_dash="dash", line_color="#666666")
    figure.update_layout(
        yaxis_title="Percent of ABBYY line count",
        template="plotly_white",
        margin=dict(l=50, r=30, t=50, b=100),
        showlegend=False,
    )
    figure.update_yaxes(range=[0, max(line_pct) * 1.18])
    return figure


def build_word_recovery_figure(rows: list[SheetSummary]) -> go.Figure:
    labels = [row.label for row in rows]
    word_pct = [percentage(row.paddle_word_count, row.abbyy_word_count) for row in rows]
    hover_word = [
        f"Paddle {row.paddle_word_count:,}<br>ABBYY {row.abbyy_word_count:,}"
        for row in rows
    ]

    figure = go.Figure()
    figure.add_trace(
        go.Bar(
            name="Word count vs ABBYY",
            x=labels,
            y=word_pct,
            text=[f"{value:.1f}%" for value in word_pct],
            textposition="outside",
            hovertemplate="%{x}<br>%{customdata}<extra></extra>",
            customdata=hover_word,
            marker_color="#55A630",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=[],
            y=[],
            mode="markers",
            showlegend=False,
        )
    )
    figure.add_hline(y=100, line_dash="dash", line_color="#666666")
    figure.update_layout(
        yaxis_title="Percent of ABBYY word count",
        template="plotly_white",
        margin=dict(l=50, r=30, t=50, b=100),
        showlegend=False,
    )
    figure.update_yaxes(range=[0, max(word_pct) * 1.18])
    return figure


def build_absolute_word_count_figure(rows: list[SheetSummary]) -> go.Figure:
    labels = ["ABBYY", *[row.label for row in rows]]
    values = [rows[0].abbyy_word_count, *[row.paddle_word_count for row in rows]]
    colors = [
        "#6C757D",
        "#33658A",
        "#55A630",
        "#BC4749",
        "#FF9F1C",
        "#6A4C93",
        "#1982C4",
    ][: len(labels)]

    figure = go.Figure()
    figure.add_trace(
        go.Bar(
            x=labels,
            y=values,
            text=[f"{value:,}" for value in values],
            textposition="outside",
            marker_color=colors,
            hovertemplate="%{x}<br>Word count: %{y:,}<extra></extra>",
            showlegend=False,
        )
    )
    figure.update_layout(
        yaxis_title="Whole-page word count",
        template="plotly_white",
        margin=dict(l=60, r=30, t=50, b=100),
    )
    figure.update_yaxes(range=[0, max(values) * 1.15])
    return figure


def build_artifact_totals_figure(rows: list[SheetSummary]) -> go.Figure:
    labels = [row.label for row in rows]
    paddle_values = [row.paddle_artifact_entries for row in rows]
    abbyy_values = [row.abbyy_artifact_entries for row in rows]

    figure = go.Figure()
    figure.add_trace(
        go.Bar(
            name="Paddle workflow",
            x=labels,
            y=paddle_values,
            text=paddle_values,
            textposition="outside",
            marker_color="#BC4749",
        )
    )
    figure.add_trace(
        go.Scatter(
            name="ABBYY baseline",
            x=labels,
            y=abbyy_values,
            mode="lines+markers+text",
            text=[str(value) for value in abbyy_values],
            textposition="top center",
            line=dict(color="#6C757D", width=3, dash="dash"),
            marker=dict(color="#6C757D", size=9),
        )
    )
    figure.update_layout(
        yaxis_title="Artifact-entry count",
        template="plotly_white",
        margin=dict(l=50, r=30, t=50, b=80),
    )
    return figure


def build_artifact_category_vs_abbyy_figure(rows: list[SheetSummary]) -> go.Figure:
    error_types = list(rows[0].paddle_error_counts.keys())
    subplot_titles = [row.label for row in rows]
    figure = make_subplots(
        rows=len(rows),
        cols=1,
        subplot_titles=subplot_titles,
        vertical_spacing=0.045,
    )

    colors = ["#33658A", "#55A630", "#BC4749", "#FF9F1C", "#6A4C93", "#1982C4"]
    max_ratio = 0.0
    for index, row in enumerate(rows):
        ratios = [
            percentage(
                row.paddle_error_counts[error_type],
                max(1, row.abbyy_error_counts[error_type]),
            )
            if row.abbyy_error_counts[error_type] > 0
            else (100.0 if row.paddle_error_counts[error_type] == 0 else row.paddle_error_counts[error_type] * 100.0)
            for error_type in error_types
        ]
        max_ratio = max(max_ratio, max(ratios))
        customdata = [
            [
                row.paddle_error_counts[error_type],
                row.abbyy_error_counts[error_type],
            ]
            for error_type in error_types
        ]
        subplot_row = index + 1
        figure.add_trace(
            go.Bar(
                x=ratios,
                y=error_types,
                orientation="h",
                marker_color=colors[index % len(colors)],
                customdata=customdata,
                hovertemplate=(
                    "%{y}<br>"
                    "Paddle: %{customdata[0]}<br>"
                    "ABBYY: %{customdata[1]}<br>"
                    "Percent of ABBYY: %{x:.1f}%"
                    "<extra></extra>"
                ),
                showlegend=False,
            ),
            row=subplot_row,
            col=1,
        )
        figure.add_vline(
            x=100,
            line_dash="dash",
            line_color="#666666",
            row=subplot_row,
            col=1,
        )

    max_range = max(140.0, min(max_ratio * 1.12, 400.0))
    figure.update_layout(
        template="plotly_white",
        margin=dict(l=130, r=40, t=70, b=80),
        height=max(1500, 240 * len(rows)),
    )
    for row_index in range(1, len(rows) + 1):
        figure.update_xaxes(
            title_text="Percent of ABBYY",
            range=[0, max_range],
            row=row_index,
            col=1,
        )
        figure.update_yaxes(autorange="reversed", row=row_index, col=1)
    return figure


def build_human_scatter_figure(rows: list[HumanSummary]) -> go.Figure:
    figure = go.Figure()
    label_offsets = {
        "ABBYY": dict(ax=0, ay=-38, xanchor="center"),
        "PaddleOCR + Chandra": dict(ax=0, ay=-38, xanchor="center"),
        "PaddleOCR + PaddleVL": dict(ax=0, ay=-42, xanchor="center"),
        "PaddleOCR + DeepSeek": dict(ax=0, ay=-34, xanchor="center"),
        "PaddleOCR (No VL)": dict(ax=18, ay=-34, xanchor="left"),
        "PaddleOCR + olmOCR": dict(ax=0, ay=-38, xanchor="center"),
    }
    for row in rows:
        x_value = row.wer * 100
        y_value = row.cer * 100
        figure.add_trace(
            go.Scatter(
                x=[x_value],
                y=[y_value],
                mode="markers",
                marker=dict(
                    size=22 + row.word_accuracy * 28,
                    color=row.word_accuracy * 100,
                    colorscale="Viridis",
                    showscale=False,
                    line=dict(width=1, color="#333333"),
                ),
                customdata=[[row.word_accuracy * 100, row.word_edits, row.substitutions, row.insertions, row.deletions]],
                hovertemplate=(
                    f"{row.label}<br>"
                    "Word accuracy: %{customdata[0]:.2f}%<br>"
                    "WER: %{x:.2f}%<br>"
                    "CER: %{y:.2f}%<br>"
                    "Word edits: %{customdata[1]}<br>"
                    "S/I/D: %{customdata[2]}/%{customdata[3]}/%{customdata[4]}"
                    "<extra></extra>"
                ),
                name=row.label,
            )
        )
        offset = label_offsets.get(row.label, dict(ax=0, ay=-36, xanchor="center"))
        figure.add_annotation(
            x=x_value,
            y=y_value,
            text=row.label,
            showarrow=False,
            xanchor=offset["xanchor"],
            yanchor="bottom",
            xshift=offset["ax"],
            yshift=-offset["ay"],
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor="rgba(60,60,60,0.35)",
            borderwidth=1,
            borderpad=3,
            font=dict(size=11, color="#1f3b64"),
        )
    x_values = [row.wer * 100 for row in rows]
    y_values = [row.cer * 100 for row in rows]
    x_min = max(0, min(x_values) - 0.55)
    x_max = max(x_values) + 0.55
    y_min = max(0, min(y_values) - 0.35)
    y_max = max(y_values) + 0.55
    figure.update_layout(
        xaxis_title="WER (%)",
        yaxis_title="CER (%)",
        template="plotly_white",
        showlegend=False,
        margin=dict(l=70, r=70, t=60, b=70),
    )
    figure.update_xaxes(range=[x_min, x_max], automargin=True)
    figure.update_yaxes(range=[y_min, y_max], automargin=True)
    return figure


def build_edit_breakdown_figure(rows: list[HumanSummary]) -> go.Figure:
    ordered = sorted(rows, key=lambda row: row.rank)
    labels = [row.label for row in ordered]
    substitutions = [row.substitutions for row in ordered]
    insertions = [row.insertions for row in ordered]
    deletions = [row.deletions for row in ordered]

    figure = go.Figure()
    figure.add_trace(
        go.Bar(
            name="Substitutions",
            x=labels,
            y=substitutions,
            marker_color="#3A86FF",
        )
    )
    figure.add_trace(
        go.Bar(
            name="Insertions",
            x=labels,
            y=insertions,
            marker_color="#FFBE0B",
        )
    )
    figure.add_trace(
        go.Bar(
            name="Deletions",
            x=labels,
            y=deletions,
            marker_color="#FB5607",
        )
    )
    figure.update_layout(
        barmode="stack",
        yaxis_title="Word edits",
        template="plotly_white",
        margin=dict(l=60, r=30, t=50, b=90),
    )
    return figure


def build_dashboard_html(
    figures: list[tuple[str, str, str, go.Figure]],
    paddle_vs_abbyy_path: Path,
    first_article_path: Path,
) -> str:
    generated = datetime.now(timezone.utc).isoformat()
    sections: list[str] = []
    include_plotlyjs = True
    for _slug, title, description, figure in figures:
        section_html = to_html(
            figure,
            include_plotlyjs=include_plotlyjs,
            full_html=False,
            config={"responsive": True, "displaylogo": False},
        )
        include_plotlyjs = False
        sections.append(
            "\n".join(
                [
                    "<section class='chart-block'>",
                    f"<h2>{html.escape(title)}</h2>",
                    f"<p>{html.escape(description)}</p>",
                    section_html,
                    "</section>",
                ]
            )
        )

    return "\n".join(
        [
            "<!DOCTYPE html>",
            "<html lang='en'>",
            "<head>",
            "<meta charset='utf-8'>",
            "<meta name='viewport' content='width=device-width, initial-scale=1'>",
            "<title>OCR Evaluation Dashboard</title>",
            "<style>",
            "body { font-family: Segoe UI, Arial, sans-serif; margin: 0; background: #f7f7f7; color: #111; }",
            "main { max-width: 1400px; margin: 0 auto; padding: 24px; }",
            "header { margin-bottom: 24px; }",
            "h1 { margin: 0 0 8px; }",
            "p { line-height: 1.5; }",
            ".chart-block { background: #fff; border: 1px solid #ddd; padding: 20px; margin-bottom: 20px; border-radius: 10px; }",
            "code { background: #f0f0f0; padding: 2px 5px; border-radius: 4px; }",
            "</style>",
            "</head>",
            "<body>",
            "<main>",
            "<header>",
            "<h1>OCR Evaluation Dashboard</h1>",
            "<p>Generated from the workbook outputs used in this repo's testing section.</p>",
            f"<p><strong>Generated:</strong> {html.escape(generated)}</p>",
            f"<p><strong>Inputs:</strong> <code>{html.escape(str(paddle_vs_abbyy_path))}</code><br>"
            f"<code>{html.escape(str(first_article_path))}</code></p>",
            "</header>",
            *sections,
            "</main>",
            "</body>",
            "</html>",
        ]
    )


def write_png_exports(
    figures: list[tuple[str, str, str, go.Figure]],
    output_dir: Path,
) -> None:
    for slug, _title, _description, figure in figures:
        output_path = output_dir / f"{slug}.png"
        width = 1600
        height = 900
        if slug == "artifact_categories":
            height = 1400
        write_image(figure, output_path, format="png", width=width, height=height, scale=2)


def friendly_human_label(value: str) -> str:
    lower = value.lower()
    if value == "abbyy":
        return "ABBYY"
    if "chandra" in lower:
        return "PaddleOCR + Chandra"
    if "paddlevl" in lower:
        return "PaddleOCR + PaddleVL"
    if "deepseek" in lower:
        return "PaddleOCR + DeepSeek"
    if "olmocr" in lower:
        return "PaddleOCR + olmOCR"
    if "ppcor-preproccess-3x2-docparse" in lower:
        return "PaddleOCR (No VL)"
    return f"PaddleOCR + {value}"


def friendly_whole_page_label(value: str) -> str:
    lower = value.strip().lower()
    mapping = {
        "preprocess only": "PaddleOCR + Preprocess only",
        "tiling only": "PaddleOCR (No VL)",
        "deepseek": "PaddleOCR + DeepSeek",
        "olmocr": "PaddleOCR + olmOCR",
        "chandra": "PaddleOCR + Chandra",
        "paddlevl": "PaddleOCR + PaddleVL",
    }
    return mapping.get(lower, f"PaddleOCR + {value}")


def parse_int(value: object) -> int:
    if value is None:
        return 0
    if isinstance(value, int):
        return value
    text = str(value).strip().replace(",", "")
    return int(float(text)) if text else 0


def parse_float(value: object) -> float:
    if value is None:
        return 0.0
    if isinstance(value, float):
        return value
    if isinstance(value, int):
        return float(value)
    text = str(value).strip().replace("%", "")
    return float(text) if text else 0.0


def percentage(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return (numerator / denominator) * 100.0


if __name__ == "__main__":
    main()
