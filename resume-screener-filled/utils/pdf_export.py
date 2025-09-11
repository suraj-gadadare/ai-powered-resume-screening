from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO

def export_report_pdf(df, jd_text: str) -> bytes:
    """Generate a simple, readable PDF report from the dataframe."""
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=24, leftMargin=24, topMargin=24, bottomMargin=24)
    styles = getSampleStyleSheet()
    elems = []

    elems.append(Paragraph("AI Resume Screening Report", styles["Title"]))
    elems.append(Spacer(1, 12))
    if jd_text:
        elems.append(Paragraph("Job Description (excerpt):", styles["Heading3"]))
        excerpt = (jd_text[:600] + "…") if len(jd_text) > 600 else jd_text
        elems.append(Paragraph(excerpt.replace("\n","<br/>"), styles["BodyText"]))
        elems.append(Spacer(1, 12))

    # Build table
    cols = ["Resume", "Final Score", "Semantic Match %", "Skill Match %", "Experience (yrs)", "Top Skills"]
    data = [cols]
    for _, r in df.iterrows():
        data.append([
            str(r.get("Resume","")),
            str(r.get("Final Score","")),
            str(r.get("Semantic Match %","")),
            str(r.get("Skill Match %","")),
            str(r.get("Experience (yrs)","")),
            str(r.get("Top Skills",""))[:120]
        ])

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#444")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.whitesmoke),
        ("ALIGN", (1,1), (-2,-1), "CENTER"),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,0), 10),
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.whitesmoke, colors.HexColor("#f7f7f7")]),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
    ]))
    elems.append(table)
    doc.build(elems)
    buf.seek(0)
    return buf.getvalue()