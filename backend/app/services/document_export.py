"""Export document content_json to Markdown or HTML."""

from datetime import datetime


def content_json_to_markdown(content_json: dict) -> str:
    """Convert content_json to a Markdown document."""
    doc_type = content_json.get("type", "document")
    metadata = content_json.get("metadata", {})
    sections = content_json.get("sections", [])

    lines = []
    lines.append(f"# CONCEPT — {doc_type.replace('_', ' ').title()}")
    lines.append("")

    if metadata.get("confidence_note"):
        lines.append(f"> **{metadata['confidence_note']}**")
        lines.append("")

    for section in sections:
        lines.append(f"## {section.get('title', 'Sectie')}")
        lines.append("")
        lines.append(section.get("content", ""))
        lines.append("")

    lines.append("---")
    lines.append("")
    if metadata.get("generated_by"):
        lines.append(f"*Gegenereerd door: {metadata['generated_by']}*")
    lines.append(f"*Geexporteerd op: {datetime.now().strftime('%Y-%m-%d %H:%M')}*")

    return "\n".join(lines)


def content_json_to_html(content_json: dict) -> str:
    """Convert content_json to a standalone HTML document with print-friendly styling."""
    import html

    doc_type = content_json.get("type", "document")
    metadata = content_json.get("metadata", {})
    sections = content_json.get("sections", [])

    title = f"CONCEPT — {doc_type.replace('_', ' ').title()}"
    generated_by = metadata.get("generated_by", "onbekend")
    confidence = metadata.get("confidence_note", "AI CONCEPT — verifieer handmatig")
    export_date = datetime.now().strftime("%Y-%m-%d %H:%M")

    sections_html = ""
    for section in sections:
        sec_title = html.escape(section.get("title", "Sectie"))
        sec_content = html.escape(section.get("content", "")).replace("\n", "<br>")
        sections_html += f"""
        <section>
          <h2>{sec_title}</h2>
          <p>{sec_content}</p>
        </section>"""

    return f"""<!DOCTYPE html>
<html lang="nl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(title)}</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      font-family: 'Inter', -apple-system, sans-serif;
      max-width: 800px;
      margin: 0 auto;
      padding: 2rem;
      color: #1f2937;
      line-height: 1.7;
    }}
    h1 {{
      font-size: 1.6rem;
      font-weight: 700;
      margin-bottom: 0.5rem;
      color: #111827;
    }}
    .concept-badge {{
      display: inline-block;
      background: #fef2f2;
      color: #b91c1c;
      border: 1px solid #fecaca;
      padding: 0.3rem 0.8rem;
      border-radius: 6px;
      font-size: 0.8rem;
      font-weight: 600;
      margin-bottom: 1.5rem;
    }}
    h2 {{
      font-size: 1.1rem;
      font-weight: 600;
      margin-top: 2rem;
      margin-bottom: 0.5rem;
      color: #374151;
      border-bottom: 1px solid #e5e7eb;
      padding-bottom: 0.3rem;
    }}
    section p {{
      font-size: 0.95rem;
      color: #4b5563;
      margin-bottom: 1rem;
    }}
    .footer {{
      margin-top: 3rem;
      padding-top: 1rem;
      border-top: 1px solid #e5e7eb;
      font-size: 0.8rem;
      color: #9ca3af;
    }}
    @media print {{
      body {{ padding: 1cm; }}
      .concept-badge {{ background: #fff; border: 2px solid #b91c1c; }}
    }}
  </style>
</head>
<body>
  <h1>{html.escape(title)}</h1>
  <div class="concept-badge">{html.escape(confidence)}</div>
  {sections_html}
  <div class="footer">
    <p>Gegenereerd door: {html.escape(generated_by)}</p>
    <p>Geexporteerd op: {export_date}</p>
  </div>
</body>
</html>"""
