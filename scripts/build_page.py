"""Build docs/index.html from paper/paper.md, so the page and the paper cannot disagree.
Paper figures (paper/figures/*.png) are shown from docs/assets/figures/, where scripts/s06_figures.py writes them.

    python scripts/build_paper.py && python scripts/build_page.py
"""
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIG = re.compile(r"!\[(\*\*Figure (\d+)\.\*\* )?(.*?)\]\(docs/(assets/figures/[^)]+)\)")

EXPLORE = """<h3 id="explore">3.4 Explore the data</h3>
<p>The map shows the storage trend of each 1-degree GRACE cell from 2002 to 2026. Select a cell, or use Tab, to read its value. The solid outline is the Lake Chad sink catchment and the dashed outline the larger level-3 unit. A 1-degree cell is finer than what GRACE resolves (a few hundred kilometres), so neighbouring cells are not independent.</p>
<div id="gr-map" class="gr-map"></div>
<div class="gr-legend"><span id="gr-lim-lo"></span><span id="gr-bar" class="gr-bar" aria-hidden="true"></span><span id="gr-lim-hi"></span></div>
<p id="gr-readout" class="gr-readout" role="status">Select a cell for its trend.</p>
<p>The chart shows the monthly series for the Lake Chad sink catchment. Use the buttons to show or hide each series. Lines break where GRACE has no month.</p>
<div id="gr-toggles" class="gr-toggles" role="group" aria-label="Series"></div>
<div id="gr-chart" class="gr-chart"></div>
"""


def image_size(rel):
    from PIL import Image
    with Image.open(ROOT / "docs" / rel) as im:
        return im.size


def figure_html(m):
    num, desc, src = m.group(2), m.group(3), m.group(4)
    alt = re.sub(r"\*\*", "", desc).replace('"', "&quot;")
    w, h = image_size(src)
    return (f'<figure class="wide" id="fig-{num}"><img src="{src}" width="{w}" height="{h}" loading="lazy" alt="{alt}">'
            f'<figcaption><b>Figure {num}.</b> {desc}</figcaption></figure>')


def tidy(html):
    parts = re.split(r"(<[^>]+>)", html)
    unit = re.compile(r"(\d) (mm|km|km²|km³|%)")
    return "".join(p if p.startswith("<") else unit.sub("\\1\u00a0\\2", p) for p in parts)


def main():
    md = (ROOT / "paper" / "paper.md").read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", md, flags=re.S)
    meta = dict(re.findall(r'^(\w+): "?([^"\n]*)"?$', m.group(1), flags=re.M)) if m else {}
    body = FIG.sub(figure_html, md[m.end():] if m else md)
    tmp = ROOT / "paper" / "_page_body.md"
    tmp.write_text(body, encoding="utf-8")
    out = ROOT / "docs" / "index.html"
    try:
        subprocess.run(["pandoc", str(tmp), "-f", "markdown-raw_html+raw_html", "-t", "html5", "--shift-heading-level-by=1",
                        "--template", str(ROOT / "scripts" / "page_template.html"), "-o", str(out),
                        "--metadata", f"pagetitle={meta.get('title', '')}", "--metadata", f"title={meta.get('title', '')}",
                        "--metadata", f"author={meta.get('author', '')}", "--metadata", f"date={meta.get('date', '')}",
                        "--metadata", "description=GRACE water storage over the Lake Chad sink catchment, 2002-2026: trend, uncertainty and what is groundwater."],
                       check=True)
    finally:
        tmp.unlink(missing_ok=True)
    html = out.read_text(encoding="utf-8")
    marker = '<h2 id="discussion">'
    if html.count(marker) != 1:
        raise SystemExit("discussion heading not found")
    out.write_text(tidy(html.replace(marker, EXPLORE + marker)), encoding="utf-8")
    print("wrote", out)


if __name__ == "__main__":
    main()
