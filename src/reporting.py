from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ALGORITHM_NAMES = {
    "ucs": "Custo Uniforme",
    "dls": "Profundidade Limitada",
    "greedy": "Procura Sôfrega",
    "astar": "A*",
}


def build_pdf_report(output_path: str | Path, payload: dict):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    styles = getSampleStyleSheet()

    title = ParagraphStyle(
        "TitleCustom",
        parent=styles["Title"],
        alignment=TA_CENTER,
        textColor=colors.HexColor("#123b5d"),
        spaceAfter=10,
    )

    h1 = ParagraphStyle(
        "H1Custom",
        parent=styles["Heading1"],
        textColor=colors.HexColor("#123b5d"),
        spaceBefore=12,
        spaceAfter=8,
    )

    body = ParagraphStyle(
        "BodyCustom",
        parent=styles["BodyText"],
        leading=15,
        spaceAfter=6,
    )

    table_cell = ParagraphStyle(
        "TableCell",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        spaceAfter=0,
    )

    table_cell_center = ParagraphStyle(
        "TableCellCenter",
        parent=table_cell,
        alignment=TA_CENTER,
    )

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=1.8 * cm,
        leftMargin=1.8 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )

    story = []

    def p(text: str, style=table_cell):
        return Paragraph(text, style)

    story.append(
        Paragraph(
            f"Relatório de Execução — Procura entre {payload['origin']} e {payload['goal']}",
            title,
        )
    )
    story.append(Paragraph(f"Timestamp: {payload['timestamp']}", body))
    story.append(
        Paragraph(
            f"Matrícula autenticada: <b>{payload['vehicle'].get('detected_plate', 'N/D')}</b>",
            body,
        )
    )
    story.append(Spacer(1, 0.4 * cm))

    # Resumo dos algoritmos
    story.append(Paragraph("Resumo dos algoritmos", h1))

    summary_table_data = [[
        p("Algoritmo", table_cell_center),
        p("Caminho final"),
        p("Distância", table_cell_center),
        p("Nós expandidos", table_cell_center),
        p("Sucesso", table_cell_center),
    ]]

    for name, result in payload["results"].items():
        pretty_name = ALGORITHM_NAMES.get(name, name)
        final_path = " → ".join(result["path"]) if result["path"] else "Sem caminho"

        summary_table_data.append([
            p(pretty_name, table_cell_center),
            p(final_path),
            p(str(result["cost"]), table_cell_center),
            p(str(result["expanded_nodes"]), table_cell_center),
            p("Sim" if result["success"] else "Não", table_cell_center),
        ])

    summary_table = Table(
        summary_table_data,
        colWidths=[3.2 * cm, 7.2 * cm, 2.1 * cm, 3.0 * cm, 1.8 * cm],
    )
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#123b5d")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (2, 1), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#7a8a99")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
            colors.whitesmoke,
            colors.HexColor("#eef3f7"),
        ]),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 0.4 * cm))

    # Iterações
    label_map = {
        "g": "Custo acumulado (g)",
        "h": "Heurística (h)",
        "f": "Custo total (f = g + h)",
        "depth": "Profundidade",
        "stack_size_after_pop": "Tamanho da pilha",
        "frontier_size_after_pop": "Tamanho da fronteira",
    }

    for name, result in payload["results"].items():
        pretty_name = ALGORITHM_NAMES.get(name, name)

        story.append(Paragraph(f"Iterações — {pretty_name}", h1))
        story.append(
            Paragraph(
                f"Caminho final: {' → '.join(result['path']) if result['path'] else 'Sem caminho'}",
                body,
            )
        )
        story.append(Paragraph(f"Distância final: {result['cost']}", body))
        story.append(
            Paragraph(
                f"Número de iterações registadas: {len(result['iterations'])}",
                body,
            )
        )

        iter_table_data = [[
            p("#", table_cell_center),
            p("Cidade expandida"),
            p("Caminho"),
            p("Valores"),
        ]]

        for idx, item in enumerate(result["iterations"][:20], start=1):
            metrics_lines = []
            for k, v in item.items():
                if k not in {"expanded_city", "path"}:
                    label = label_map.get(k, k.replace("_", " ").capitalize())
                    metrics_lines.append(f"{label}: {v}")

            metrics = "<br/>".join(metrics_lines)
            path_text = " → ".join(item.get("path", []))

            iter_table_data.append([
                p(str(idx), table_cell_center),
                p(item.get("expanded_city", "")),
                p(path_text),
                p(metrics),
            ])

        iter_table = Table(
            iter_table_data,
            colWidths=[0.9 * cm, 3.0 * cm, 6.5 * cm, 5.3 * cm],
        )
        iter_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#d7e4ef")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#8da2b5")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
                colors.white,
                colors.HexColor("#f6f9fc"),
            ]),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(iter_table)
        story.append(Spacer(1, 0.3 * cm))

    # Atrações
    story.append(PageBreak())
    story.append(Paragraph("Atrações principais", h1))

    for city, items in payload["attractions"].items():
        story.append(Paragraph(city, styles["Heading2"]))
        for item in items:
            story.append(
                Paragraph(
                    f"<b>{item['name']}</b> — {item['description']}",
                    body,
                )
            )

    doc.build(story)