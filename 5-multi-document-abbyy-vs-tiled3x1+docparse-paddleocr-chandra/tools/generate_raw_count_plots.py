#!/usr/bin/env python3
"""Generate raw line-count and word-count charts for the three OCR runs."""

from __future__ import annotations

import argparse
import html
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from plotly import graph_objects as go
from plotly.io import to_html, write_image


REPO_ROOT = Path(__file__).resolve().parent.parent
EVAL_ROOT = REPO_ROOT.parent
DEFAULT_RUNS = [
    (
        "ABBYY",
        EVAL_ROOT / "3-multi-document-abbyy-vs-tiled3x1+docparse-paddleocr-paddlevl" / "test-data" / "abbyy",
    ),
    (
        "3x1 + docparse + PaddleOCR + PaddleVL",
        EVAL_ROOT
        / "3-multi-document-abbyy-vs-tiled3x1+docparse-paddleocr-paddlevl"
        / "test-data"
        / "preprocessing-tiling_3x1_dp+paddleocr+vl+clean",
    ),
    (
        "3x1 + docparse + PaddleOCR + Chandra",
        REPO_ROOT / "test-data",
    ),
]
DEFAULT_OUTPUT_HTML = REPO_ROOT / "test-results" / "plots" / "chandra_vs_paddlevl_raw_counts_dashboard.html"
DEFAULT_OUTPUT_PNG_DIR = REPO_ROOT / "test-results" / "plots" / "png" / "chandra_vs_paddlevl_raw_counts"
RUN_COLORS = {
    "ABBYY": "#6C757D",
    "3x1 + docparse + PaddleOCR + PaddleVL": "#1982C4",
    "3x1 + docparse + PaddleOCR + Chandra": "#55A630",
}


@dataclass(frozen=True)
class DocumentCounts:
    document: str
    line_count: int
    word_count: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run",
        action="append",
        metavar="LABEL=PATH",
        help="Override runs to compare. May be passed multiple times.",
    )
    parser.add_argument("--output-html", type=Path, default=DEFAULT_OUTPUT_HTML)
    parser.add_argument("--output-png-dir", type=Path, default=DEFAULT_OUTPUT_PNG_DIR)
    return parser.parse_args()


def parse_run(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise ValueError(f"Run must be LABEL=PATH, got: {value}")
    label, raw_path = value.split("=", 1)
    cleaned_label = " ".join(label.split())
    if not cleaned_label:
        raise ValueError("Run label must not be empty.")
    path = Path(raw_path.strip())
    if not path.exists():
        raise FileNotFoundError(path)
    return cleaned_label, path.resolve()


def iter_document_dirs(base_dir: Path) -> list[Path]:
    return sorted(path for path in base_dir.iterdir() if path.is_dir())


def iter_ocr_txt_files(document_dir: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(document_dir.glob("*.txt")):
        name = path.name.lower()
        if name.endswith(".post_ocr_vl_progress.txt"):
            continue
        if "b4-cleaned" in name:
            continue
        files.append(path)
    return files


def read_counts(path: Path) -> tuple[int, int]:
    text = path.read_text(encoding="utf-8", errors="replace")
    nonblank_line_count = sum(1 for line in text.splitlines() if line.strip())
    word_count = len(text.split())
    return nonblank_line_count, word_count


def collect_run_counts(base_dir: Path) -> dict[str, DocumentCounts]:
    counts: dict[str, DocumentCounts] = {}
    for document_dir in iter_document_dirs(base_dir):
        line_total = 0
        word_total = 0
        for path in iter_ocr_txt_files(document_dir):
            lines, words = read_counts(path)
            line_total += lines
            word_total += words
        counts[document_dir.name] = DocumentCounts(
            document=document_dir.name,
            line_count=line_total,
            word_count=word_total,
        )
    return counts


def build_count_figure(
    document_names: list[str],
    run_labels: list[str],
    run_counts: dict[str, dict[str, DocumentCounts]],
    metric: str,
    yaxis_title: str,
) -> go.Figure:
    figure = go.Figure()
    for label in run_labels:
        figure.add_trace(
            go.Bar(
                name=label,
                x=document_names,
                y=[getattr(run_counts[label][document], metric) for document in document_names],
                marker_color=RUN_COLORS.get(label),
            )
        )
    figure.update_layout(
        barmode="group",
        yaxis_title=yaxis_title,
        template="plotly_white",
        margin=dict(l=60, r=30, t=50, b=110),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    return figure


def build_dashboard_html(
    figures: list[tuple[str, str, str, go.Figure]],
    run_labels: list[str],
    document_names: list[str],
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
                    "<div class='figure-wrap'>",
                    section_html,
                    "</div>",
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
            "<title>Raw OCR Count Dashboard</title>",
            "<style>",
            "body { font-family: Segoe UI, Arial, sans-serif; margin: 0; background: #f7f7f7; color: #111; }",
            "main { max-width: 1400px; margin: 0 auto; padding: 24px; }",
            "header { margin-bottom: 24px; }",
            "h1 { margin: 0 0 8px; }",
            "p { line-height: 1.5; }",
            ".chart-block { background: #fff; border: 1px solid #ddd; padding: 20px; margin: 0 auto 20px; border-radius: 10px; max-width: 1260px; }",
            ".figure-wrap { width: min(100%, 1120px); margin: 0 auto; }",
            "</style>",
            "</head>",
            "<body>",
            "<main>",
            "<header>",
            "<h1>Raw OCR Count Dashboard</h1>",
            f"<p>Absolute nonblank line counts and word counts for {', '.join(html.escape(label) for label in run_labels)}.</p>",
            f"<p><strong>Generated:</strong> {html.escape(generated)}</p>",
            f"<p><strong>Scope:</strong> {len(document_names)} documents.</p>",
            "</header>",
            *sections,
            "</main>",
            "</body>",
            "</html>",
        ]
    )


def write_png_exports(figures: list[tuple[str, str, str, go.Figure]], output_dir: Path) -> None:
    for slug, _title, _description, figure in figures:
        write_image(figure, output_dir / f"{slug}.png", format="png", width=1600, height=900, scale=2)


def main() -> None:
    args = parse_args()
    runs = [parse_run(value) for value in args.run] if args.run else [(label, path.resolve()) for label, path in DEFAULT_RUNS]
    if len(runs) < 2:
        raise ValueError("At least two runs are required.")

    run_counts = {label: collect_run_counts(path) for label, path in runs}
    document_names = sorted({document for counts in run_counts.values() for document in counts})
    run_labels = [label for label, _path in runs]

    missing: list[str] = []
    for label in run_labels:
        for document in document_names:
            if document not in run_counts[label]:
                missing.append(f"{label}: {document}")
    if missing:
        raise ValueError("Missing document counts for some runs: " + ", ".join(missing))

    figures = [
        (
            "document_line_counts",
            "Raw Nonblank Line Counts by Document",
            "Absolute nonblank line counts for ABBYY, 3x1 + PaddleVL, and 3x1 + Chandra, computed directly from the TXT outputs.",
            build_count_figure(document_names, run_labels, run_counts, "line_count", "Document nonblank line count"),
        ),
        (
            "document_word_counts",
            "Raw Word Counts by Document",
            "Absolute word counts for ABBYY, 3x1 + PaddleVL, and 3x1 + Chandra, computed directly from the TXT outputs.",
            build_count_figure(document_names, run_labels, run_counts, "word_count", "Document word count"),
        ),
    ]

    output_html = args.output_html.resolve()
    output_png_dir = args.output_png_dir.resolve()
    output_html.parent.mkdir(parents=True, exist_ok=True)
    output_png_dir.mkdir(parents=True, exist_ok=True)
    output_html.write_text(build_dashboard_html(figures, run_labels, document_names), encoding="utf-8")
    write_png_exports(figures, output_png_dir)
    print(f"Wrote {output_html}")
    print(f"Wrote PNG charts to {output_png_dir}")


if __name__ == "__main__":
    main()
