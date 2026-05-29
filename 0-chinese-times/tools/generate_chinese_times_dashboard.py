#!/usr/bin/env python3
"""Generate a bilingual Plotly dashboard for the Chinese Times OCR workbook."""

from __future__ import annotations

import argparse
import html
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from openpyxl import load_workbook
from plotly import graph_objects as go
from plotly.io import to_html


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_WORKBOOK = REPO_ROOT / "chinese_times_test_case.xlsx"
DEFAULT_OUTPUT_HTML = REPO_ROOT / "plots" / "chinese_times_ocr_dashboard.html"


STRINGS = {
    "en": {
        "dashboard_title": "Chinese Times OCR Comparison Dashboard",
        "dashboard_desc": (
            "Manual comparison dashboard for ABBYY FineReader Server 14 and "
            "PaddleOCR on a small Chinese Times test set."
        ),
        "generated": "Generated",
        "inputs": "Input workbook",
        "english_section": "English Charts",
        "french_section": "Graphiques en français",
        "summary_title": "Dataset Snapshot",
        "summary_desc": (
            "This workbook contains 20 manually scored test cases across two "
            "Chinese Times issues. Scores are 0, 0.5, or 1 per tool."
        ),
        "cases": "Cases",
        "issues": "Newspaper issues",
        "paddle_total": "Paddle total",
        "abbyy_total": "ABBYY total",
        "points": "points",
        "scenario_chart_title": "Scenario Strengths by OCR Tool",
        "scenario_chart_desc": (
            "Each row combines the two cases for one scenario. This is the "
            "best high-level view of where Paddle or ABBYY is stronger."
        ),
        "scenario_axis": "Total score across two cases",
        "difference_chart_title": "Scenario Advantage Chart",
        "difference_chart_desc": (
            "This chart collapses the comparison into one number per scenario: "
            "Paddle minus ABBYY. Bars to the right favor Paddle; bars to the "
            "left favor ABBYY."
        ),
        "difference_axis": "Paddle minus ABBYY",
        "matrix_chart_title": "Win Matrix by Scenario and Newspaper Issue",
        "matrix_chart_desc": (
            "Each cell shows whether Paddle won, ABBYY won, or both tools tied "
            "for one scenario in one newspaper issue."
        ),
        "distribution_chart_title": "Pass / Partial / Fail Profile",
        "distribution_chart_desc": (
            "A compact view of score quality for each tool across all 20 test "
            "cases."
        ),
        "distribution_axis": "Number of cases",
        "case_chart_title": "Case-Level Score Heatmap",
        "case_chart_desc": (
            "Rows show all 20 manual test cases. The heatmap makes ties, "
            "partial matches, and clear wins visible at a glance."
        ),
        "issue_chart_title": "Totals by Newspaper Issue",
        "issue_chart_desc": (
            "Issue-level totals show that the June 18, 1948 sample favors "
            "Paddle more strongly than the June 12 sample."
        ),
        "issue_axis": "Total score",
        "outcome_chart_title": "Head-to-Head Outcome Count",
        "outcome_chart_desc": (
            "A simple summary of how many cases Paddle won, ABBYY won, or tied."
        ),
        "outcome_axis": "Number of cases",
        "abbyy": "ABBYY",
        "paddle": "PaddleOCR",
        "tie": "Tie",
        "paddle_win": "Paddle win",
        "abbyy_win": "ABBYY win",
        "score": "Score",
        "gap_vs_abbyy": "Paddle minus ABBYY",
        "gap_vs_paddle": "ABBYY minus Paddle",
        "win_status": "Win status",
        "pass": "Pass",
        "partial": "Partial",
        "fail": "Fail",
        "scenario": "Scenario",
        "issue": "Issue",
        "case_id": "Case ID",
        "test_data": "Test data",
        "expected": "Expected",
        "remarks": "Remarks",
        "no_remarks": "No remarks",
        "score_scale": "Score scale: 0 = fail, 0.5 = partial, 1 = pass",
    },
    "fr": {
        "dashboard_title": "Tableau de bord de comparaison OCR du Chinese Times",
        "dashboard_desc": (
            "Tableau de bord de comparaison manuelle entre ABBYY FineReader "
            "Server 14 et PaddleOCR pour un petit échantillon du Chinese Times."
        ),
        "generated": "Généré",
        "inputs": "Classeur source",
        "english_section": "Charts in English",
        "french_section": "Graphiques en français",
        "summary_title": "Aperçu du jeu de données",
        "summary_desc": (
            "Ce classeur contient 20 cas de test évalués manuellement dans "
            "deux numéros du Chinese Times. Les scores sont 0, 0,5 ou 1."
        ),
        "cases": "Cas",
        "issues": "Numéros de journaux",
        "paddle_total": "Total Paddle",
        "abbyy_total": "Total ABBYY",
        "points": "points",
        "scenario_chart_title": "Forces par scénario selon l’outil OCR",
        "scenario_chart_desc": (
            "Chaque ligne regroupe les deux cas d’un même scénario. C’est la "
            "meilleure vue d’ensemble pour voir où Paddle ou ABBYY domine."
        ),
        "scenario_axis": "Score total sur deux cas",
        "difference_chart_title": "Avantage par scénario",
        "difference_chart_desc": (
            "Ce graphique résume la comparaison en un nombre par scénario : "
            "Paddle moins ABBYY. Les barres à droite favorisent Paddle; les "
            "barres à gauche favorisent ABBYY."
        ),
        "difference_axis": "Paddle moins ABBYY",
        "matrix_chart_title": "Matrice des gains par scénario et numéro de journal",
        "matrix_chart_desc": (
            "Chaque case montre si Paddle a gagné, si ABBYY a gagné ou si les "
            "deux outils sont à égalité pour un scénario dans un numéro donné."
        ),
        "distribution_chart_title": "Profil réussite / partiel / échec",
        "distribution_chart_desc": (
            "Une vue compacte de la qualité des scores pour chaque outil sur "
            "les 20 cas de test."
        ),
        "distribution_axis": "Nombre de cas",
        "case_chart_title": "Carte thermique des scores par cas",
        "case_chart_desc": (
            "Les lignes montrent les 20 cas de test manuels. La carte "
            "thermique rend visibles les égalités, les correspondances "
            "partielles et les victoires nettes."
        ),
        "issue_chart_title": "Totaux par numéro du journal",
        "issue_chart_desc": (
            "Les totaux par numéro montrent que l’échantillon du 18 juin 1948 "
            "favorise plus nettement Paddle que celui du 12 juin."
        ),
        "issue_axis": "Score total",
        "outcome_chart_title": "Résultats tête-à-tête",
        "outcome_chart_desc": (
            "Un résumé simple du nombre de cas gagnés par Paddle, par ABBYY ou "
            "terminés à égalité."
        ),
        "outcome_axis": "Nombre de cas",
        "abbyy": "ABBYY",
        "paddle": "PaddleOCR",
        "tie": "Égalité",
        "paddle_win": "Victoire Paddle",
        "abbyy_win": "Victoire ABBYY",
        "score": "Score",
        "gap_vs_abbyy": "Paddle moins ABBYY",
        "gap_vs_paddle": "ABBYY moins Paddle",
        "win_status": "Résultat",
        "pass": "Réussite",
        "partial": "Partiel",
        "fail": "Échec",
        "scenario": "Scénario",
        "issue": "Numéro",
        "case_id": "ID du cas",
        "test_data": "Donnée testée",
        "expected": "Résultat attendu",
        "remarks": "Remarques",
        "no_remarks": "Aucune remarque",
        "score_scale": "Échelle: 0 = échec, 0,5 = partiel, 1 = réussite",
    },
}


SCENARIO_META = {
    "person_name": {
        "en": "Personal name recognition",
        "fr": "Reconnaissance des noms de personnes",
        "order": 1,
    },
    "image_text": {
        "en": "Text in image titles",
        "fr": "Texte dans les titres en image",
        "order": 2,
    },
    "unclear_phrase": {
        "en": "Unclear phrase recognition",
        "fr": "Reconnaissance des expressions peu nettes",
        "order": 3,
    },
    "uncommon_words": {
        "en": "Rare or uncommon characters",
        "fr": "Caractères rares ou peu courants",
        "order": 4,
    },
    "column_title": {
        "en": "Column title recognition",
        "fr": "Reconnaissance des titres de colonne",
        "order": 5,
    },
    "column_sentence": {
        "en": "Sentence in a column",
        "fr": "Phrase dans une colonne",
        "order": 6,
    },
    "year": {
        "en": "Year and date strings",
        "fr": "Chaînes d’année et de date",
        "order": 7,
    },
    "location": {
        "en": "Geographic location",
        "fr": "Lieu géographique",
        "order": 8,
    },
    "advertising": {
        "en": "Advertising content",
        "fr": "Contenu publicitaire",
        "order": 9,
    },
    "english": {
        "en": "English-language content",
        "fr": "Contenu en anglais",
        "order": 10,
    },
}


ISSUE_META = {
    "sfu.00001_19480612.1": {
        "en": "June 12, 1948 issue",
        "fr": "Numéro du 12 juin 1948",
        "short_en": "1948-06-12",
        "short_fr": "1948-06-12",
    },
    "sfu.00001_19480618.1": {
        "en": "June 18, 1948 issue",
        "fr": "Numéro du 18 juin 1948",
        "short_en": "1948-06-18",
        "short_fr": "1948-06-18",
    },
}


@dataclass(frozen=True)
class CaseRow:
    issue_key: str
    case_id: str
    scenario_key: str
    scenario_source: str
    test_data: str
    expected_result: str
    abbyy_actual: str
    abbyy_score: float
    paddle_actual: str
    paddle_score: float
    remarks: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a bilingual Plotly dashboard for Chinese Times OCR testing."
    )
    parser.add_argument(
        "--workbook",
        type=Path,
        default=DEFAULT_WORKBOOK,
        help="Path to chinese_times_test_case.xlsx",
    )
    parser.add_argument(
        "--output-html",
        type=Path,
        default=DEFAULT_OUTPUT_HTML,
        help="Output HTML dashboard path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    workbook_path = args.workbook.resolve()
    output_html = args.output_html.resolve()
    output_html.parent.mkdir(parents=True, exist_ok=True)

    cases = load_cases(workbook_path)
    figures_en = build_figures(cases, "en")
    figures_fr = build_figures(cases, "fr")
    html_text = build_dashboard_html(cases, figures_en, figures_fr, workbook_path)
    output_html.write_text(html_text, encoding="utf-8")
    print(f"Wrote {output_html}")


def load_cases(path: Path) -> list[CaseRow]:
    workbook = load_workbook(path, data_only=True)
    cases: list[CaseRow] = []

    for worksheet in workbook.worksheets:
        if worksheet.max_row <= 1:
            continue
        if not str(worksheet.title).startswith("sfu.00001_"):
            continue
        for row in worksheet.iter_rows(min_row=2, values_only=True):
            if not any(value is not None for value in row):
                continue
            case_id = clean_text(row[1])
            if not case_id:
                continue
            scenario_source = clean_text(row[2])
            cases.append(
                CaseRow(
                    issue_key=worksheet.title,
                    case_id=case_id,
                    scenario_key=canonicalize_scenario(scenario_source),
                    scenario_source=scenario_source,
                    test_data=clean_text(row[3]),
                    expected_result=clean_text(row[4]),
                    abbyy_actual=clean_text(row[5]),
                    abbyy_score=parse_float(row[6]),
                    paddle_actual=clean_text(row[7]),
                    paddle_score=parse_float(row[8]),
                    remarks=clean_text(row[9]),
                )
            )
    return sorted(cases, key=lambda item: (item.issue_key, item.case_id))


def build_figures(cases: list[CaseRow], lang: str) -> list[tuple[str, str, str, go.Figure]]:
    return [
        (
            "scenario_strengths",
            t(lang, "scenario_chart_title"),
            t(lang, "scenario_chart_desc"),
            build_scenario_grouped_bar_figure(cases, lang),
        ),
        (
            "scenario_advantage",
            t(lang, "difference_chart_title"),
            t(lang, "difference_chart_desc"),
            build_scenario_difference_figure(cases, lang),
        ),
        (
            "win_matrix",
            t(lang, "matrix_chart_title"),
            t(lang, "matrix_chart_desc"),
            build_win_matrix_figure(cases, lang),
        ),
        (
            "score_distribution",
            t(lang, "distribution_chart_title"),
            t(lang, "distribution_chart_desc"),
            build_score_distribution_figure(cases, lang),
        ),
        (
            "case_heatmap",
            t(lang, "case_chart_title"),
            t(lang, "case_chart_desc"),
            build_case_heatmap_figure(cases, lang),
        ),
        (
            "issue_totals",
            t(lang, "issue_chart_title"),
            t(lang, "issue_chart_desc"),
            build_issue_totals_figure(cases, lang),
        ),
        (
            "outcomes",
            t(lang, "outcome_chart_title"),
            t(lang, "outcome_chart_desc"),
            build_outcome_figure(cases, lang),
        ),
    ]


def build_scenario_grouped_bar_figure(cases: list[CaseRow], lang: str) -> go.Figure:
    grouped: dict[str, dict[str, float]] = defaultdict(lambda: {"abbyy": 0.0, "paddle": 0.0})
    for case in cases:
        grouped[case.scenario_key]["abbyy"] += case.abbyy_score
        grouped[case.scenario_key]["paddle"] += case.paddle_score

    ordered_keys = sorted(
        grouped,
        key=lambda key: (
            grouped[key]["paddle"] - grouped[key]["abbyy"],
            grouped[key]["paddle"],
            -SCENARIO_META[key]["order"],
        ),
        reverse=True,
    )
    labels = [SCENARIO_META[key][lang] for key in ordered_keys]
    abbyy_scores = [grouped[key]["abbyy"] for key in ordered_keys]
    paddle_scores = [grouped[key]["paddle"] for key in ordered_keys]
    score_gaps = [paddle - abbyy for abbyy, paddle in zip(abbyy_scores, paddle_scores)]

    figure = go.Figure()
    figure.add_trace(
        go.Bar(
            x=abbyy_scores,
            y=labels,
            orientation="h",
            name=t(lang, "abbyy"),
            marker_color="#1F4E79",
            customdata=[[gap] for gap in score_gaps],
            hovertemplate=(
                f"{t(lang, 'abbyy')}: %{{x:.1f}}<br>"
                f"{t(lang, 'gap_vs_paddle')}: %{{customdata[0]:+.1f}}"
                "<extra></extra>"
            ),
        )
    )
    figure.add_trace(
        go.Bar(
            x=paddle_scores,
            y=labels,
            orientation="h",
            name=t(lang, "paddle"),
            marker_color="#D97706",
            customdata=[[gap] for gap in score_gaps],
            hovertemplate=(
                f"{t(lang, 'paddle')}: %{{x:.1f}}<br>"
                f"{t(lang, 'gap_vs_abbyy')}: %{{customdata[0]:+.1f}}"
                "<extra></extra>"
            ),
        )
    )
    figure.update_layout(
        template="plotly_white",
        barmode="group",
        xaxis_title=t(lang, "scenario_axis"),
        margin=dict(l=70, r=40, t=30, b=110),
        height=660,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    figure.update_xaxes(range=[0, 2.1], dtick=0.5, automargin=True)
    figure.update_yaxes(automargin=True)
    figure.add_annotation(
        x=0,
        y=-0.1,
        xref="paper",
        yref="paper",
        text=t(lang, "score_scale"),
        showarrow=False,
        align="left",
        font=dict(size=12, color="#4A5568"),
    )
    return figure


def build_case_heatmap_figure(cases: list[CaseRow], lang: str) -> go.Figure:
    row_labels = [build_case_label(case, lang) for case in cases]
    z_values = [[case.abbyy_score, case.paddle_score] for case in cases]
    customdata = [
        [
            [
                issue_label(case.issue_key, lang, short=False),
                SCENARIO_META[case.scenario_key][lang],
                case.case_id,
                case.test_data,
                case.expected_result,
                case.abbyy_actual,
                case.remarks or t(lang, "no_remarks"),
            ],
            [
                issue_label(case.issue_key, lang, short=False),
                SCENARIO_META[case.scenario_key][lang],
                case.case_id,
                case.test_data,
                case.expected_result,
                case.paddle_actual,
                case.remarks or t(lang, "no_remarks"),
            ],
        ]
        for case in cases
    ]

    figure = go.Figure(
        data=
        [
            go.Heatmap(
                z=z_values,
                x=[t(lang, "abbyy"), t(lang, "paddle")],
                y=row_labels,
                customdata=customdata,
                zmin=0,
                zmax=1,
                colorscale=[
                    [0.0, "#B91C1C"],
                    [0.5, "#F4C95D"],
                    [1.0, "#15803D"],
                ],
                colorbar=dict(
                    title=t(lang, "score"),
                    tickmode="array",
                    tickvals=[0, 0.5, 1],
                    ticktext=["0", "0.5", "1"],
                ),
                hovertemplate=(
                    f"{t(lang, 'issue')}: %{{customdata[0]}}<br>"
                    f"{t(lang, 'scenario')}: %{{customdata[1]}}<br>"
                    f"{t(lang, 'case_id')}: %{{customdata[2]}}<br>"
                    f"{t(lang, 'test_data')}: %{{customdata[3]}}<br>"
                    f"{t(lang, 'expected')}: %{{customdata[4]}}<br>"
                    "OCR: %{customdata[5]}<br>"
                    f"{t(lang, 'remarks')}: %{{customdata[6]}}<br>"
                    f"{t(lang, 'score')}: %{{z:.1f}}"
                    "<extra></extra>"
                ),
            )
        ]
    )
    figure.update_layout(
        template="plotly_white",
        margin=dict(l=70, r=40, t=30, b=60),
        height=860,
    )
    figure.update_xaxes(side="top")
    figure.update_yaxes(autorange="reversed", automargin=True)
    return figure


def build_scenario_difference_figure(cases: list[CaseRow], lang: str) -> go.Figure:
    grouped: dict[str, dict[str, float]] = defaultdict(lambda: {"abbyy": 0.0, "paddle": 0.0})
    for case in cases:
        grouped[case.scenario_key]["abbyy"] += case.abbyy_score
        grouped[case.scenario_key]["paddle"] += case.paddle_score

    ordered_keys = sorted(
        grouped,
        key=lambda key: (
            grouped[key]["paddle"] - grouped[key]["abbyy"],
            grouped[key]["paddle"],
            grouped[key]["abbyy"],
        ),
        reverse=True,
    )
    labels = [SCENARIO_META[key][lang] for key in ordered_keys]
    differences = [grouped[key]["paddle"] - grouped[key]["abbyy"] for key in ordered_keys]
    colors = [
        "#D97706" if value > 0 else "#1F4E79" if value < 0 else "#9CA3AF"
        for value in differences
    ]

    figure = go.Figure(
        data=[
            go.Bar(
                x=differences,
                y=labels,
                orientation="h",
                marker_color=colors,
                text=[f"{value:+.1f}" for value in differences],
                textposition="outside",
                customdata=[
                    [grouped[key]["abbyy"], grouped[key]["paddle"]]
                    for key in ordered_keys
                ],
                hovertemplate=(
                    f"{t(lang, 'abbyy')}: %{{customdata[0]:.1f}}<br>"
                    f"{t(lang, 'paddle')}: %{{customdata[1]:.1f}}<br>"
                    f"{t(lang, 'difference_axis')}: %{{x:+.1f}}"
                    "<extra></extra>"
                ),
            )
        ]
    )
    max_abs = max(1.0, max(abs(value) for value in differences) + 0.2)
    figure.add_vline(x=0, line_width=2, line_color="#6B7280")
    figure.update_layout(
        template="plotly_white",
        xaxis_title=t(lang, "difference_axis"),
        margin=dict(l=70, r=40, t=30, b=70),
        height=620,
        showlegend=False,
    )
    figure.update_xaxes(range=[-max_abs, max_abs], dtick=0.5, automargin=True)
    figure.update_yaxes(automargin=True)
    return figure


def build_win_matrix_figure(cases: list[CaseRow], lang: str) -> go.Figure:
    issue_keys = sorted({case.issue_key for case in cases})
    scenario_keys = sorted({case.scenario_key for case in cases}, key=lambda key: SCENARIO_META[key]["order"])
    issue_labels = [issue_label(issue_key, lang, short=True) for issue_key in issue_keys]
    scenario_labels = [SCENARIO_META[key][lang] for key in scenario_keys]

    case_lookup = {(case.scenario_key, case.issue_key): case for case in cases}
    z_values: list[list[int]] = []
    customdata: list[list[list[object]]] = []
    for scenario_key in scenario_keys:
        z_row: list[int] = []
        data_row: list[list[object]] = []
        for issue_key in issue_keys:
            case = case_lookup[(scenario_key, issue_key)]
            if case.paddle_score > case.abbyy_score:
                z_row.append(1)
                status = t(lang, "paddle_win")
            elif case.paddle_score < case.abbyy_score:
                z_row.append(-1)
                status = t(lang, "abbyy_win")
            else:
                z_row.append(0)
                status = t(lang, "tie")
            data_row.append(
                [
                    issue_label(issue_key, lang, short=False),
                    SCENARIO_META[scenario_key][lang],
                    case.case_id,
                    case.abbyy_score,
                    case.paddle_score,
                    status,
                    case.remarks or t(lang, "no_remarks"),
                ]
            )
        z_values.append(z_row)
        customdata.append(data_row)

    figure = go.Figure(
        data=[
            go.Heatmap(
                z=z_values,
                x=issue_labels,
                y=scenario_labels,
                customdata=customdata,
                zmin=-1,
                zmax=1,
                colorscale=[
                    [0.0, "#1F4E79"],
                    [0.5, "#E5E7EB"],
                    [1.0, "#D97706"],
                ],
                colorbar=dict(
                    title=t(lang, "win_status"),
                    tickmode="array",
                    tickvals=[-1, 0, 1],
                    ticktext=[t(lang, "abbyy_win"), t(lang, "tie"), t(lang, "paddle_win")],
                ),
                hovertemplate=(
                    f"{t(lang, 'issue')}: %{{customdata[0]}}<br>"
                    f"{t(lang, 'scenario')}: %{{customdata[1]}}<br>"
                    f"{t(lang, 'case_id')}: %{{customdata[2]}}<br>"
                    f"{t(lang, 'abbyy')}: %{{customdata[3]:.1f}}<br>"
                    f"{t(lang, 'paddle')}: %{{customdata[4]:.1f}}<br>"
                    f"{t(lang, 'win_status')}: %{{customdata[5]}}<br>"
                    f"{t(lang, 'remarks')}: %{{customdata[6]}}"
                    "<extra></extra>"
                ),
            )
        ]
    )
    figure.update_layout(
        template="plotly_white",
        margin=dict(l=70, r=40, t=30, b=60),
        height=560,
    )
    figure.update_yaxes(autorange="reversed", automargin=True)
    return figure


def build_score_distribution_figure(cases: list[CaseRow], lang: str) -> go.Figure:
    buckets = [("fail", 0.0), ("partial", 0.5), ("pass", 1.0)]
    counts = {
        "abbyy": Counter(case.abbyy_score for case in cases),
        "paddle": Counter(case.paddle_score for case in cases),
    }

    figure = go.Figure()
    colors = {"fail": "#B91C1C", "partial": "#F4C95D", "pass": "#15803D"}
    for key, value in buckets:
        figure.add_trace(
            go.Bar(
                x=[counts["abbyy"][value], counts["paddle"][value]],
                y=[t(lang, "abbyy"), t(lang, "paddle")],
                orientation="h",
                name=t(lang, key),
                marker_color=colors[key],
                hovertemplate=f"{t(lang, key)}: %{{x}}<extra></extra>",
            )
        )

    figure.update_layout(
        template="plotly_white",
        barmode="stack",
        xaxis_title=t(lang, "distribution_axis"),
        margin=dict(l=70, r=30, t=30, b=60),
        height=360,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    figure.update_xaxes(range=[0, len(cases)], dtick=2)
    return figure


def build_issue_totals_figure(cases: list[CaseRow], lang: str) -> go.Figure:
    grouped: dict[str, dict[str, float]] = defaultdict(lambda: {"abbyy": 0.0, "paddle": 0.0})
    for case in cases:
        grouped[case.issue_key]["abbyy"] += case.abbyy_score
        grouped[case.issue_key]["paddle"] += case.paddle_score

    issue_keys = sorted(grouped)
    labels = [issue_label(issue_key, lang, short=True) for issue_key in issue_keys]
    abbyy_scores = [grouped[issue_key]["abbyy"] for issue_key in issue_keys]
    paddle_scores = [grouped[issue_key]["paddle"] for issue_key in issue_keys]

    figure = go.Figure()
    figure.add_trace(
        go.Bar(
            x=labels,
            y=abbyy_scores,
            name=t(lang, "abbyy"),
            marker_color="#1F4E79",
            hovertemplate=f"{t(lang, 'abbyy')}: %{{y:.1f}}<extra></extra>",
        )
    )
    figure.add_trace(
        go.Bar(
            x=labels,
            y=paddle_scores,
            name=t(lang, "paddle"),
            marker_color="#D97706",
            hovertemplate=f"{t(lang, 'paddle')}: %{{y:.1f}}<extra></extra>",
        )
    )
    figure.update_layout(
        template="plotly_white",
        barmode="group",
        yaxis_title=t(lang, "issue_axis"),
        margin=dict(l=60, r=30, t=30, b=70),
        height=480,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    figure.update_yaxes(range=[0, 6.2], dtick=1)
    return figure


def build_outcome_figure(cases: list[CaseRow], lang: str) -> go.Figure:
    outcomes = Counter()
    for case in cases:
        if case.paddle_score > case.abbyy_score:
            outcomes["paddle_win"] += 1
        elif case.paddle_score < case.abbyy_score:
            outcomes["abbyy_win"] += 1
        else:
            outcomes["tie"] += 1

    keys = ["paddle_win", "abbyy_win", "tie"]
    labels = [t(lang, key) for key in keys]
    values = [outcomes.get(key, 0) for key in keys]
    colors = ["#D97706", "#1F4E79", "#6B7280"]

    figure = go.Figure(
        data=[
            go.Bar(
                x=labels,
                y=values,
                marker_color=colors,
                text=values,
                textposition="outside",
                hovertemplate="%{x}: %{y}<extra></extra>",
            )
        ]
    )
    figure.update_layout(
        template="plotly_white",
        yaxis_title=t(lang, "outcome_axis"),
        margin=dict(l=60, r=30, t=30, b=70),
        height=430,
        showlegend=False,
    )
    figure.update_yaxes(range=[0, max(values) + 2], dtick=2)
    return figure


def build_dashboard_html(
    cases: list[CaseRow],
    figures_en: list[tuple[str, str, str, go.Figure]],
    figures_fr: list[tuple[str, str, str, go.Figure]],
    workbook_path: Path,
) -> str:
    generated = datetime.now(timezone.utc).isoformat()
    sections_en, include_plotlyjs = build_dashboard_sections(figures_en, include_plotlyjs=True)
    sections_fr, _ = build_dashboard_sections(figures_fr, include_plotlyjs=include_plotlyjs)

    summary_en = build_summary_block(cases, "en")
    summary_fr = build_summary_block(cases, "fr")

    return "\n".join(
        [
            "<!DOCTYPE html>",
            "<html lang='en'>",
            "<head>",
            "<meta charset='utf-8'>",
            "<meta name='viewport' content='width=device-width, initial-scale=1'>",
            f"<title>{html.escape(t('en', 'dashboard_title'))}</title>",
            "<style>",
            ":root { --bg: #eef2f7; --ink: #10233b; --muted: #516173; --card: #ffffff; --border: #d7dee7; --accent: #d97706; --accent-2: #1f4e79; }",
            "body { font-family: Segoe UI, Arial, sans-serif; margin: 0; background: radial-gradient(circle at top left, #f6efe4 0, #eef2f7 32%, #e7edf5 100%); color: var(--ink); }",
            "main { max-width: 1400px; margin: 0 auto; padding: 28px 24px 40px; }",
            "header { margin-bottom: 28px; padding: 28px; background: linear-gradient(135deg, #fff8ef 0%, #ffffff 52%, #edf4fb 100%); border: 1px solid var(--border); border-radius: 18px; }",
            "h1 { margin: 0 0 10px; font-size: clamp(2rem, 4vw, 3rem); }",
            "h2 { margin-top: 0; }",
            "p { line-height: 1.55; color: var(--muted); }",
            ".chart-block { background: var(--card); border: 1px solid var(--border); padding: 20px; margin: 0 auto 20px; border-radius: 14px; max-width: 1260px; box-shadow: 0 8px 24px rgba(16, 35, 59, 0.05); }",
            ".language-section { margin-top: 30px; }",
            ".language-section > h2 { max-width: 1260px; margin-left: auto; margin-right: auto; }",
            ".figure-wrap { width: min(100%, 1120px); margin: 0 auto; }",
            ".summary-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 14px; margin-top: 18px; }",
            ".summary-card { background: linear-gradient(180deg, #fff 0%, #f8fafc 100%); border: 1px solid var(--border); border-radius: 12px; padding: 16px; }",
            ".summary-card strong { display: block; font-size: 0.9rem; color: var(--muted); margin-bottom: 8px; }",
            ".summary-card span { font-size: 1.85rem; font-weight: 700; color: var(--ink); }",
            "code { background: #edf2f7; padding: 2px 5px; border-radius: 4px; }",
            "</style>",
            "</head>",
            "<body>",
            "<main>",
            "<header>",
            f"<h1>{html.escape(t('en', 'dashboard_title'))}</h1>",
            f"<p>{html.escape(t('en', 'dashboard_desc'))}</p>",
            f"<p><strong>{html.escape(t('en', 'generated'))}:</strong> {html.escape(generated)}</p>",
            f"<p><strong>{html.escape(t('en', 'inputs'))}:</strong> <code>{html.escape(str(workbook_path))}</code></p>",
            "</header>",
            f"<section class='language-section'><h2>{html.escape(t('en', 'english_section'))}</h2>",
            summary_en,
            *sections_en,
            "</section>",
            f"<section class='language-section'><h2>{html.escape(t('fr', 'french_section'))}</h2>",
            summary_fr,
            *sections_fr,
            "</section>",
            "</main>",
            "</body>",
            "</html>",
        ]
    )


def build_dashboard_sections(
    figures: list[tuple[str, str, str, go.Figure]],
    include_plotlyjs: bool,
) -> tuple[list[str], bool]:
    sections: list[str] = []
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
                    f"<h3>{html.escape(title)}</h3>",
                    f"<p>{html.escape(description)}</p>",
                    "<div class='figure-wrap'>",
                    section_html,
                    "</div>",
                    "</section>",
                ]
            )
        )
    return sections, include_plotlyjs


def build_summary_block(cases: list[CaseRow], lang: str) -> str:
    abbyy_total = sum(case.abbyy_score for case in cases)
    paddle_total = sum(case.paddle_score for case in cases)
    issue_count = len({case.issue_key for case in cases})

    cards = [
        (t(lang, "cases"), str(len(cases))),
        (t(lang, "issues"), str(issue_count)),
        (t(lang, "abbyy_total"), f"{abbyy_total:.1f}"),
        (t(lang, "paddle_total"), f"{paddle_total:.1f}"),
    ]
    card_html = "\n".join(
        [
            "<div class='summary-grid'>",
            *[
                (
                    "<div class='summary-card'>"
                    f"<strong>{html.escape(label)}</strong>"
                    f"<span>{html.escape(value)}</span>"
                    "</div>"
                )
                for label, value in cards
            ],
            "</div>",
        ]
    )
    return "\n".join(
        [
            "<section class='chart-block'>",
            f"<h3>{html.escape(t(lang, 'summary_title'))}</h3>",
            f"<p>{html.escape(t(lang, 'summary_desc'))}</p>",
            card_html,
            "</section>",
        ]
    )


def build_case_label(case: CaseRow, lang: str) -> str:
    return (
        f"{issue_label(case.issue_key, lang, short=True)} | "
        f"{case.case_id} | {SCENARIO_META[case.scenario_key][lang]}"
    )


def issue_label(issue_key: str, lang: str, short: bool) -> str:
    issue = ISSUE_META.get(issue_key, {})
    if short:
        return issue.get(f"short_{lang}", issue_key)
    return issue.get(lang, issue_key)


def canonicalize_scenario(value: str) -> str:
    normalized = re.sub(r"\s+", " ", value.strip().lower())
    mapping = {
        "verify a person's name": "person_name",
        "verify that words display in an image of the test item": "image_text",
        "verify an unclear phrase": "unclear_phrase",
        "verify an uncommon words": "uncommon_words",
        "verify a column's title": "column_title",
        "verify a sentence in a column": "column_sentence",
        "verify a year": "year",
        "verify a geographic location": "location",
        "verify a dvertising content": "advertising",
        "verify an english content": "english",
    }
    if normalized not in mapping:
        raise ValueError(f"Unknown scenario label: {value!r}")
    return mapping[normalized]


def clean_text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip().replace("\r\n", "\n").replace("\r", "\n")


def parse_float(value: object) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace("%", "")
    return float(text) if text else 0.0


def t(lang: str, key: str) -> str:
    return STRINGS[lang][key]


if __name__ == "__main__":
    main()
