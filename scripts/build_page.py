"""Build docs/index.html from paper/paper.md, so the page and the paper cannot disagree.
Paper figures (paper/figures/*.png) are shown from docs/assets/figures/, where scripts/s06_figures.py writes them.

    python scripts/build_paper.py && python scripts/build_page.py
"""
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIG = re.compile(r"!\[(\*\*Figure (\d+)\.\*\* )?(.*?)\]\(docs/(assets/figures/[^)]+)\)")

EXPLORE = """<h3 id="explore">3.4 Map and chart</h3>
<p>The map shows the straight-line storage trend of each 1-degree GRACE cell from 2002 to 2026. Select a cell to read its value; with a keyboard, press Tab to reach the map and use the arrow keys. The solid outline is the level-3 basin unit and the dashed outline the western level-4 unit. A 1-degree cell is finer than what GRACE resolves (a few hundred kilometres), so neighbouring cells are not independent.</p>
<div id="gr-map" class="gr-map"></div>
<div class="gr-legend"><span class="gr-legend-title">Trend, mm per year</span><span id="gr-lim-lo"></span><span id="gr-bar" class="gr-bar" aria-hidden="true"></span><span id="gr-lim-hi"></span></div>
<p id="gr-readout" class="gr-readout" role="status" aria-live="polite">Select a cell for its trend.</p>
<details class="gr-cells"><summary>Show the cells in the basin unit as a table</summary><div id="gr-table"></div></details>
<p>The chart shows the monthly series for the basin unit. Use the buttons to show or hide each series. Lines break where GRACE has no month.</p>
<div id="gr-toggles" class="gr-toggles" role="group" aria-label="Series shown in the chart"></div>
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
                        "--metadata", "description=GRACE water storage over the Lake Chad basin, 2002-2026: when it changed, by how much, and what is groundwater."],
                       check=True)
    finally:
        tmp.unlink(missing_ok=True)
    html = out.read_text(encoding="utf-8")
    marker = '<h2 id="discussion">'
    if html.count(marker) != 1:
        raise SystemExit("discussion heading not found")
    out.write_text(_study_links(_page_end(tidy(html.replace(marker, EXPLORE + marker))), out.parent), encoding="utf-8")
    print("wrote", out)



def _study_links(html, docs):
    """Re-insert the cross-site links that the portfolio's tools/sync_nav.py keeps in docs/assets/study-*.html."""
    import re as _re
    for key, where in (("study-bar", "top"), ("study-nav", "end")):
        f = docs / "assets" / f"{key}.html"
        if not f.exists():
            continue
        block = f.read_text(encoding="utf-8").strip()
        html = _re.sub(rf"<!-- {key}:start -->.*?<!-- {key}:end -->\n?", "", html, flags=_re.S)
        if where == "top":
            html = _re.sub(r"(<body[^>]*>)", lambda m: m.group(1) + "\n" + block, html, count=1)
        else:
            html = html.replace("</body>", block + "\n</body>", 1)
    f = docs / "assets" / "study-others.html"  # the "Other studies" line in the footer, kept in place
    if f.exists():
        block = f.read_text(encoding="utf-8").strip()
        html = _re.sub(r"<!-- study-others:start -->.*?<!-- study-others:end -->", lambda m: block, html, flags=_re.S)
    return html


def _web_ending(html, end):
    """Shape the end of the page like the other study sites: the paper's own data-and-code section becomes the
    opening paragraph of "Data, code and citation" (so the page says it once), the page end goes before the
    references, and the references become the same compact list, with DOIs shown as doi:..."""
    import re as _re
    m = _re.search(r'<h2 id="[^"]*data-and-code[^"]*">.*?</h2>\s*(.*?)(?=<h2 )', html, flags=_re.S)
    if not m:
        raise SystemExit("page end: the paper's data-and-code section was not found (its heading id changed?)")
    html = html[:m.start()] + html[m.end():]
    end, n = _re.subn(r'(<h2 id="h-dc">.*?</h2>)', lambda k: k.group(1) + "\n    " + m.group(1).strip(), end, count=1, flags=_re.S)
    if not n:
        raise SystemExit('page end: page_end.html has no <h2 id="h-dc"> heading')
    anchor = '<h2 id="references">'
    if anchor not in html:
        raise SystemExit("page end: no References heading to place the end of the page before")
    html = html.replace(anchor, end + "\n" + anchor, 1)
    r = _re.search(r'(<h2 id="references">References</h2>\s*)((?:<p>.*?</p>\s*)+)', html, flags=_re.S)
    if not r:
        raise SystemExit("page end: no reference paragraphs after the References heading")
    else:
        def item(p):
            p = " ".join(p.split())  # pandoc wraps lines, even inside tags
            p = _re.sub(r'<a href="https://doi\.org/([^"]+)"[^>]*>[^<]*</a>', lambda k: f'<a href="https://doi.org/{k.group(1)}">doi:{k.group(1)}</a>', p)
            trim = lambda u: (u[:-1] if u.endswith(")") and u.count("(") < u.count(")") else u).rstrip(".,;:")
            def bare(k, doi):
                u = trim(k.group(1)); rest = k.group(1)[len(u):]
                return (f'<a href="https://doi.org/{u}">doi:{u}</a>' if doi else f'<a href="{u}">{u}</a>') + rest
            p = _re.sub(r'(?<![">/])https://doi\.org/([^\s<]+)', lambda k: bare(k, True), p)
            p = _re.sub(r'(?<![">/])(https?://[^\s<]+)', lambda k: bare(k, False), p)
            return "<li>" + p + "</li>"
        items = [item(p) for p in _re.findall(r"<p>(.*?)</p>", r.group(2), flags=_re.S)]
        html = html[:r.start(2)] + '<ol class="refs" role="list">\n' + "\n".join(items) + "\n</ol>\n" + html[r.end(2):]
    return html


def _page_end(html):
    """The end of the page (key terms, data and citation, a note, feedback) lives in page_end.html next to this script."""
    return _web_ending(html, Path(__file__).with_name("page_end.html").read_text(encoding="utf-8").strip())

if __name__ == "__main__":
    main()
