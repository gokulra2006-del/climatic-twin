from copy import deepcopy
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt


ROOT = Path(r"C:\Users\gokul\Desktop\PROJECTS\climatetwin")
REPORT = ROOT / "output" / "docx" / "ClimateTwin_DA2_Project_Report.docx"


def insert_before(paragraph, text, style_name=None):
    result = paragraph._parent.add_paragraph()
    result._p.getparent().remove(result._p)
    paragraph._p.addprevious(result._p)
    if style_name:
        result.style = style_name
    result.add_run(text)
    return result


def insert_after(paragraph, text, style_name=None):
    result = paragraph._parent.add_paragraph()
    result._p.getparent().remove(result._p)
    paragraph._p.addnext(result._p)
    if style_name:
        result.style = style_name
    result.add_run(text)
    return result


def font_all(doc):
    for p in doc.paragraphs:
        for run in p.runs:
            run.font.name = "Times New Roman"
            run._element.rPr.rFonts.set(qn("w:ascii"), "Times New Roman")
            run._element.rPr.rFonts.set(qn("w:hAnsi"), "Times New Roman")
            if run.font.size is None:
                run.font.size = Pt(11)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    for run in p.runs:
                        run.font.name = "Times New Roman"
                        run._element.rPr.rFonts.set(qn("w:ascii"), "Times New Roman")
                        run._element.rPr.rFonts.set(qn("w:hAnsi"), "Times New Roman")
                        if run.font.size is None:
                            run.font.size = Pt(10)


def shade(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)
    shd.set(qn("w:val"), "clear")


def set_cell_borders(cell, color="A6A6A6"):
    tc_pr = cell._tc.get_or_add_tcPr()
    borders = tc_pr.first_child_found_in("w:tcBorders")
    if borders is None:
        borders = OxmlElement("w:tcBorders")
        tc_pr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        tag = qn(f"w:{edge}")
        el = borders.find(tag)
        if el is None:
            el = OxmlElement(f"w:{edge}")
            borders.append(el)
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "6")
        el.set(qn("w:color"), color)


def format_tables(doc):
    for table in doc.tables:
        for row_index, row in enumerate(table.rows):
            for cell in row.cells:
                cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
                set_cell_borders(cell)
                shade(cell, "E7E6E6" if row_index == 0 else ("F7F7F7" if row_index % 2 == 0 else "FFFFFF"))
                for p in cell.paragraphs:
                    p.paragraph_format.space_after = Pt(1)
                    p.paragraph_format.space_before = Pt(1)
                    for run in p.runs:
                        run.font.color.rgb = None
                        run.font.name = "Times New Roman"
                        run._element.rPr.rFonts.set(qn("w:ascii"), "Times New Roman")
                        run._element.rPr.rFonts.set(qn("w:hAnsi"), "Times New Roman")
                        run.font.size = Pt(9.5)
                        run.bold = row_index == 0


def main():
    doc = Document(REPORT)
    by_text = {p.text.strip(): p for p in doc.paragraphs if p.text.strip()}

    # Make the first page state the deliverable purpose unambiguously.
    title = by_text.get("ClimateTwin") or by_text["ClimateTwin DA2 Project Report"]
    title.text = "ClimateTwin DA2 Project Report"
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in title.runs:
        run.bold = True
        run.font.size = Pt(18)

    subtitle = by_text["An Uncertainty Aware Multi Hazard Digital Twin for Climate Risk Monitoring in Chennai"]
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in subtitle.runs:
        run.italic = True
        run.font.size = Pt(12)

    # Rebuild the evidence-aware demonstration section before the results heading.
    for p in list(doc.paragraphs):
        if p.text.startswith("The following results are interpreted according to") or p.text.startswith("3.5 DA2 Demonstration Evidence") or p.text.startswith("The demonstrator presents the Flood Digital Twin dashboard"):
            p._element.getparent().remove(p._element)
    by_text = {p.text.strip(): p for p in doc.paragraphs if p.text.strip()}
    anchor = by_text["4. Results Demonstration and Discussion"]
    demo = insert_before(
        anchor,
        "The demonstrator presents the Flood Digital Twin dashboard, hazard navigation, forecast probability and quantile bands, risk category, source label, and operational status. During the captured prototype run, the dashboard explicitly reported System Offline and Simulated prototype sensor feeds. This is an intentional evidence safeguard: the screen is valid evidence of full-stack integration and transparent risk communication, while live deployment, real-time sensor health, and municipal actuation remain outside the scope of the demonstrated results.",
    )
    heading = insert_before(
        demo,
        "3.5 DA2 Demonstration Evidence",
    )
    heading.runs[0].bold = True
    heading.runs[0].font.size = Pt(12)
    insert_before(
        heading,
        "The following results are interpreted according to the evidence class recorded by the system. This is essential for the DA2 demonstration: a working user interface and backend workflow are demonstrated, but a simulated or offline dashboard state is not described as a live municipal warning service.",
    )

    # Add methodological depth required for a strong DA2 report without making
    # operational claims beyond the available validation evidence.
    for p in list(doc.paragraphs):
        if p.text.startswith("2.4 Evidence Aware Alert Policy") or p.text.startswith("The warning decision combines") or p.text.startswith("3.6 Demonstration Protocol") or p.text.startswith("A reproducible demonstration proceeds") or p.text.startswith("4.4 Evaluation Protocol") or p.text.startswith("The evaluation uses chronological") or p.text.startswith("5.2 Recommended Demonstration Sequence") or p.text.startswith("For the assessed demonstration"):
            p._element.getparent().remove(p._element)
    by_text = {p.text.strip(): p for p in doc.paragraphs if p.text.strip()}
    method_anchor = by_text["3. Full System Implementation"]
    policy_body = insert_before(
        method_anchor,
        "The warning decision combines the predicted hazard score with data quality, forecast uncertainty, and source provenance. Let r be the predicted risk, q be the quality score, and w be the uncertainty width. A warning is promoted only when r exceeds the selected hazard threshold, q is adequate for the intended use, and w is communicated with the predicted category. When a source is stale, generated, or unavailable, the system degrades the confidence label rather than silently presenting the output as a live operational alert. This evidence-aware policy is the report's core novel aspect because it connects model output to a transparent decision condition.",
    )
    policy_heading = insert_before(policy_body, "2.4 Evidence Aware Alert Policy")
    policy_heading.runs[0].bold = True
    policy_heading.runs[0].font.size = Pt(12)

    results_anchor = by_text["4. Results Demonstration and Discussion"]
    demo_body = insert_before(
        results_anchor,
        "A reproducible demonstration proceeds in four stages: start the FastAPI service, open the React dashboard, select a hazard, and inspect risk, uncertainty, source provenance, and status indicators together. The assessor should then inspect historical replay and the model-health view to confirm that the same evidence labels are preserved across the workflow. The frontend screen is evidence of the interactive user interface; backend evidence should be captured only after the API health endpoint and documentation route respond successfully. This procedure keeps interface demonstration separate from operational deployment claims.",
    )
    demo_heading = insert_before(demo_body, "3.6 Demonstration Protocol and Backend Readiness")
    demo_heading.runs[0].bold = True
    demo_heading.runs[0].font.size = Pt(12)

    discussion = by_text["The working application demonstrates that a full-stack dashboard can carry data-quality metadata through ingestion, state estimation, forecast presentation, and replay. Its strongest present value is transparency: it prevents a prototype score from looking more certain than its evidence permits. Key limitations are incomplete active-infrastructure topology, limited road-closure and service-disruption labels, a non-hydrodynamic EnKF process model, a small independent holdout-event count, and simulated cascade, transfer, and intervention experiments. These limitations are explicit design targets for the next implementation phase."]
    eval_heading = insert_after(discussion, "4.4 Evaluation Protocol and Interpretation")
    eval_heading.runs[0].bold = True
    eval_heading.runs[0].font.size = Pt(12)
    insert_after(
        eval_heading,
        "The evaluation uses chronological rather than random splits so that future information cannot leak into training. Performance is reported with F1 because the available event label is imbalanced, while reliability is assessed with Brier score and interval coverage. A credible next-stage evaluation must additionally report precision, recall, lead time, false-alarm rate, CRPS or weighted interval score, and performance separately for independent extreme events. This protocol prevents a high aggregate score from being interpreted as evidence of general operational readiness.",
    )

    final_body = insert_before(
        by_text["References"],
        "For the assessed demonstration, present the dashboard with the source-status panel visible, explain one flood-risk prediction and its uncertainty bounds, then show the corresponding backend API health and documentation pages. State whether each displayed source is live, historical, proxy, synthetic, or rule based. This sequence demonstrates both frontend and backend work while protecting the project from unsupported claims.",
    )
    final_heading = insert_before(final_body, "5.2 Recommended Demonstration Sequence")
    final_heading.runs[0].bold = True
    final_heading.runs[0].font.size = Pt(12)

    # Remove a redundant title line that made the cover look like two documents.
    old = by_text.get("Digital Assignment 2 Project Report")
    if old is not None:
        old.text = "Digital Assignment 2 DA2"
        old.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in old.runs:
            run.bold = True
            run.font.size = Pt(12)

    font_all(doc)
    format_tables(doc)
    for section in doc.sections:
        section.top_margin = section.top_margin
        section.bottom_margin = section.bottom_margin

    doc.save(REPORT)
    print(REPORT)


if __name__ == "__main__":
    main()
