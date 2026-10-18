from pathlib import Path
import re

from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import BaseDocTemplate, Frame, PageBreak, Paragraph, Spacer

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "ClimateTwin_IEEE_Submission_Safe_Draft.tex"
OUT = ROOT / "output" / "pdf" / "ClimateTwin_IEEE_Submission_Safe_Draft.pdf"


def clean(text: str) -> str:
    text = text.replace("~", " ").replace("\\&", "&").replace("--", "-")
    text = re.sub(r"\\(emph|textit|textbf|mathrm)\{([^{}]*)\}", r"\2", text)
    text = re.sub(r"\\cite\{[^}]*\}", "", text)
    text = re.sub(r"\\ref\{[^}]*\}", "", text)
    text = re.sub(r"\\label\{[^}]*\}", "", text)
    text = re.sub(r"\\[a-zA-Z]+(?:\[[^]]*\])?", "", text)
    text = text.replace("{", "").replace("}", "")
    text = re.sub(r"\s+", " ", text).strip()
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def blocks(source: str):
    source = re.sub(r"(?s)\\begin\{table\*?\}.*?\\end\{table\*?\}", "", source)
    source = re.sub(r"(?s)\\begin\{align\*?\}.*?\\end\{align\*?\}", "", source)
    source = re.sub(r"(?s)\\begin\{equation\*?\}.*?\\end\{equation\*?\}", "", source)
    source = re.sub(r"(?s)\\begin\{thebibliography\}.*?\\end\{thebibliography\}", "", source)
    title = re.search(r"\\title\{(.*?)\}", source, re.S)
    abstract = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", source, re.S)
    yield "title", clean(title.group(1) if title else "ClimateTwin")
    yield "authors", "Gokul R. and Vishvanth S. | School of Computer Science and Engineering, Vellore Institute of Technology, Chennai, India"
    if abstract:
        yield "heading", "Abstract"
        yield "body", clean(abstract.group(1))
    in_document = source.split("\\begin{document}", 1)[-1]
    in_document = re.sub(r"(?s)\\begin\{abstract\}.*?\\end\{abstract\}", "", in_document)
    in_document = re.sub(r"(?s)\\begin\{IEEEkeywords\}.*?\\end\{IEEEkeywords\}", "", in_document)
    in_document = re.sub(r"(?s)\\maketitle", "", in_document)
    chunks = re.split(r"(\\(?:sub)*section\{.*?\})", in_document, flags=re.S)
    for chunk in chunks:
        m = re.fullmatch(r"\\(sub)*section\{(.*?)\}", chunk.strip(), re.S)
        if m:
            yield "subheading" if m.group(1) else "heading", clean(m.group(2))
            continue
        for para in re.split(r"\n\s*\n", chunk):
            para = clean(para)
            if len(para) > 35 and not para.startswith("documentclass"):
                yield "body", para
    yield "heading", "References"
    bib = re.search(r"(?s)\\begin\{thebibliography\}\{.*?\}(.*?)\\end\{thebibliography\}", source)
    if bib:
        for entry in re.split(r"\\bibitem\{[^}]*\}", bib.group(1)):
            entry = clean(entry)
            if entry:
                yield "reference", entry


class Paper(BaseDocTemplate):
    def __init__(self, path):
        super().__init__(path, pagesize=A4, leftMargin=0.55*inch, rightMargin=0.55*inch,
                         topMargin=0.55*inch, bottomMargin=0.55*inch)
        gap = 0.18*inch
        width = (A4[0] - self.leftMargin - self.rightMargin - gap) / 2
        frames = [Frame(self.leftMargin, self.bottomMargin, width, A4[1]-self.topMargin-self.bottomMargin, id="L"),
                  Frame(self.leftMargin+width+gap, self.bottomMargin, width, A4[1]-self.topMargin-self.bottomMargin, id="R")]
        self.addPageTemplates([__import__('reportlab').platypus.PageTemplate(id="two", frames=frames, onPage=self.footer)])

    @staticmethod
    def footer(canvas, doc):
        canvas.setFont("Helvetica", 7)
        canvas.drawCentredString(A4[0]/2, 0.31*inch, f"ClimateTwin - IEEE submission draft - {doc.page}")


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    title = ParagraphStyle("title", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=15, leading=18, alignment=TA_CENTER, spaceAfter=7)
    authors = ParagraphStyle("authors", parent=styles["Normal"], fontName="Helvetica", fontSize=8, leading=10, alignment=TA_CENTER, spaceAfter=10)
    heading = ParagraphStyle("heading", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=9.5, leading=12, spaceBefore=7, spaceAfter=3)
    subheading = ParagraphStyle("subheading", parent=heading, fontSize=8.5, leading=10.5, spaceBefore=5)
    body = ParagraphStyle("body", parent=styles["BodyText"], fontName="Times-Roman", fontSize=7.7, leading=9.4, alignment=TA_JUSTIFY, spaceAfter=4)
    reference = ParagraphStyle("reference", parent=body, leftIndent=7, firstLineIndent=-7, fontSize=7.1, leading=8.5)
    story = []
    for kind, value in blocks(SOURCE.read_text(encoding="utf-8")):
        story.append(Paragraph(value, {"title": title, "authors": authors, "heading": heading, "subheading": subheading, "body": body, "reference": reference}[kind]))
    Paper(str(OUT)).build(story)


if __name__ == "__main__":
    main()
