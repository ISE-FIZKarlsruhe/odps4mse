# docs/_scripts/build_ontologies.py
import os, subprocess
from pathlib import Path
import mkdocs_gen_files

ROOT = Path(__file__).resolve().parents[2]

# --- CONFIG: multiple ontology directories via env (comma-separated) ---
# Example: ONTOLOGY_DIRS="Ontologies,more/ontologies,even/more"
ONTOLOGY_DIRS = [
    (ROOT / p.strip()) for p in os.environ.get("ONTOLOGY_DIRS", "Ontologies").split(",")
    if p.strip()
]

# File extensions we consider ontologies
ONTO_EXTS = (".owl", ".ttl", ".rdf", ".obo")

def run(cmd):
    subprocess.run(cmd, check=True)

def tsv_to_markdown_table(tsv_path: Path, max_rows: int | None = 200):
    """Convert a ROBOT report TSV to a Markdown table string."""
    if not tsv_path.exists():
        return "_No issues found._"
    rows = []
    with tsv_path.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if max_rows is not None and i > max_rows:
                break
            rows.append(line.rstrip("\n").split("\t"))
    if not rows:
        return "_No issues found._"
    header, body = rows[0], rows[1:]
    out = []
    out.append("| " + " | ".join(header) + " |")
    out.append("| " + " | ".join(["---"] * len(header)) + " |")
    for r in body:
        # pad row to header length, just in case
        r = (r + [""] * len(header))[:len(header)]
        out.append("| " + " | ".join(r) + " |")
    if max_rows is not None and len(rows) > max_rows + 1:
        out.append(f"\n_Note: showing first {max_rows} rows._")
    return "\n".join(out)

def robot_measure(infile: Path, outdir: Path, level: str = None):
    """
    Run ROBOT measure and return the path to the produced HTML table.
    level: 'essential' (default), 'extended', 'all', 'essential-reasoner',
           'extended-reasoner', or 'all-reasoner'
    """
    outdir.mkdir(parents=True, exist_ok=True)
    html_path = outdir / "metrics.html"

    # Config via env; fallback to 'essential'
    level = level or os.environ.get("MEASURE_LEVEL", "essential")

    # ROBOT can emit html/json/tsv/csv/yaml; we pick HTML so we can embed directly.
    # See docs: https://robot.obolibrary.org/measure.html
    run([
        "robot", "measure",
        "-i", str(infile),
        "--metrics", level,
        "--format", "html",
        "-o", str(html_path)
    ])
    return html_path

def robot_report(infile: Path, outdir: Path):
    outdir.mkdir(parents=True, exist_ok=True)
    tsv = outdir / "report.tsv"
    # ↓ do not fail the process on ERRORs; still produce the TSV
    run([
        "robot", "report",
        "-i", str(infile),
        "--fail-on", "none",
        "--output", str(tsv)
    ])
    md = tsv_to_markdown_table(tsv, max_rows=None)  # embed full report
    (outdir / "report.md").write_text(md, encoding="utf-8")
    return tsv


def robot_export_entities(infile: Path, outdir: Path):
    outdir.mkdir(parents=True, exist_ok=True)
    html_out = outdir / "entities.html"
    # One compact table with ID | LABEL | TYPE
    run([
        "robot","export","-i",str(infile),
        "--header","ID|LABEL|TYPE",
        "--export",str(html_out)
    ])
    return html_out
def sparql_entities(infile: Path, outdir: Path):
    outdir.mkdir(parents=True, exist_ok=True)
    tsv = outdir / "entities.tsv"
    md = outdir / "entities.md"

    # Minimal, robust query for ID (IRI), rdfs:label, and rdf:type
    query = r"""
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
SELECT (STR(?e) AS ?ID) (STR(?lab) AS ?LABEL) (COALESCE(STR(?t), "") AS ?TYPE)
WHERE {
  ?e rdfs:label ?lab .
  OPTIONAL { ?e rdf:type ?t . }
}
ORDER BY LCASE(?LABEL)
"""
    qfile = outdir / "entities.sparql"
    qfile.write_text(query, encoding="utf-8")

    run([
        "robot", "query",
        "-i", str(infile),
        "--query", f"{qfile}=tsv",
        str(tsv)
    ])

    md.write_text(tsv_to_markdown_table(tsv, max_rows=None), encoding="utf-8")
    return md


def make_page(infile: Path, rel_root_dir: str):
    name = infile.stem
    odir = ROOT / "docs" / "ontologies" / name
    odir.mkdir(parents=True, exist_ok=True)

    report_ok = entities_ok = metrics_ok = False
    entities_md = None
    metrics_html = None

    try:
        robot_report(infile, odir)           # already modified with --fail-on none
        report_ok = True
    except Exception:
        pass

    try:
        entities_md = sparql_entities(infile, odir)
        entities_ok = True
    except Exception:
        pass

    try:
        metrics_html = robot_measure(infile, odir)   # << NEW
        metrics_ok = True
    except Exception:
        pass

    md_path = Path(f"ontologies/{name}.md")
    with mkdocs_gen_files.open(md_path, "w") as f:
        print(f"# {name}\n", file=f)
        print(f"- **Source:** `{rel_root_dir}/{infile.name}`\n", file=f)

        if entities_ok:
            print("## Classes & Properties\n", file=f)
            print(entities_md.read_text(encoding="utf-8"), file=f)

        if metrics_ok:
            print("\n## Metrics\n", file=f)
            # Embed the ROBOT metrics HTML table
            print(metrics_html.read_text(encoding="utf-8"), file=f)
            print("\n!!! tip\n    Metrics ending with `_incl` include imported ontologies; those without `_incl` are for this ontology alone.\n", file=f)

        if report_ok:
            print("\n## QC Report\n", file=f)
            print((odir / "report.md").read_text(encoding="utf-8"), file=f)
        else:
            print("\n!!! warning \"QC report\"\n    ROBOT report could not be generated.\n", file=f)

    return md_path



def discover_files():
    found = []
    for d in ONTOLOGY_DIRS:
        if not d.exists():
            continue
        rel = str(d.relative_to(ROOT))
        for p in sorted(d.rglob("*")):
            if p.suffix.lower() in ONTO_EXTS and p.is_file():
                found.append((p, rel))
    return found

def main():
    files = discover_files()
    pages = []
    for p, relroot in files:
        pages.append((make_page(p, relroot), relroot))

    # Build index page grouped by directory
    index_md = Path("ontologies/index.md")
    with mkdocs_gen_files.open(index_md, "w") as f:
        print("# Ontologies", file=f)
        print("", file=f)
        if not pages:
            print("_No ontologies found in configured directories._", file=f)
            return
        # group by relroot
        from collections import defaultdict
        groups = defaultdict(list)
        for md, relroot in pages:
            groups[relroot].append(md)
        for relroot in sorted(groups.keys()):
            print(f"## {relroot}", file=f)
            print("", file=f)
            for md in groups[relroot]:
                print(f"- [{md.stem}]({md.name})", file=f)
            print("")

if __name__ == "__main__":
    main()
