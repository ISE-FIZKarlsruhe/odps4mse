# docs/_scripts/build_ontologies.py
import os, subprocess
from pathlib import Path
import mkdocs_gen_files

# ---------- Config ----------
ROOT = Path(__file__).resolve().parents[2]

# Multiple ontology dirs (comma-separated). Defaults to "Ontologies".
ONTOLOGY_DIRS = [
    (ROOT / p.strip()) for p in os.environ.get("ONTOLOGY_DIRS", "Ontologies").split(",")
    if p.strip()
]
ONTO_EXTS = (".owl", ".ttl", ".rdf", ".obo")

# Process ODP patterns root dir (single, but you can point it anywhere)
PATTERNS_DIR = ROOT / os.environ.get("PATTERNS_DIR", "Patterns")
PATTERN_EXTS = (".ttl", ".owl", ".rdf")

# Metrics level for robot measure
MEASURE_LEVEL = os.environ.get("MEASURE_LEVEL", "essential")  # essential|extended|all|*-reasoner

# ---------- Helpers ----------
def run(cmd):
    # Never print; let mkdocs -v show subprocess output if needed
    subprocess.run(cmd, check=True)

def tsv_to_markdown_table(tsv_path: Path, max_rows: int | None = None):
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
        r = (r + [""] * len(header))[:len(header)]
        out.append("| " + " | ".join(r) + " |")
    if max_rows is not None and len(rows) > max_rows + 1:
        out.append(f"\n_Note: showing first {max_rows} rows._")
    return "\n".join(out)

def robot_report(infile: Path, outdir: Path):
    outdir.mkdir(parents=True, exist_ok=True)
    tsv = outdir / "report.tsv"
    run([
        "robot","report",
        "-i", str(infile),
        "--fail-on","none",          # important: never fail build
        "--output", str(tsv)
    ])
    (outdir / "report.md").write_text(tsv_to_markdown_table(tsv, max_rows=None), encoding="utf-8")
    return outdir / "report.md"

def robot_measure(infile: Path, outdir: Path):
    outdir.mkdir(parents=True, exist_ok=True)
    html_path = outdir / "metrics.html"
    run([
        "robot","measure",
        "-i", str(infile),
        "--metrics", MEASURE_LEVEL,
        "--format","html",
        "-o", str(html_path),
    ])
    return html_path

def sparql_entities(infile: Path, outdir: Path):
    outdir.mkdir(parents=True, exist_ok=True)
    tsv = outdir / "entities.tsv"
    md  = outdir / "entities.md"
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
        "robot","query",
        "-i", str(infile),
        "--query", f"{qfile}=tsv",
        str(tsv)
    ])
    md.write_text(tsv_to_markdown_table(tsv, max_rows=None), encoding="utf-8")
    return md

# ---------- Ontologies ----------
def discover_ontologies():
    found = []
    for d in ONTOLOGY_DIRS:
        if not d.exists():
            continue
        rel = str(d.relative_to(ROOT))
        for p in sorted(d.rglob("*")):
            if p.suffix.lower() in ONTO_EXTS and p.is_file():
                found.append((p, rel))
    return found

def make_ontology_page(infile: Path, rel_root_dir: str):
    name = infile.stem
    odir = ROOT / "docs" / "ontologies" / name
    odir.mkdir(parents=True, exist_ok=True)

    report_ok = entities_ok = metrics_ok = False
    try:
        report_md = robot_report(infile, odir)
        report_ok = True
    except Exception:
        report_md = None
    try:
        entities_md = sparql_entities(infile, odir)
        entities_ok = True
    except Exception:
        entities_md = None
    try:
        metrics_html = robot_measure(infile, odir)
        metrics_ok = True
    except Exception:
        metrics_html = None

    md_path = Path(f"ontologies/{name}.md")
    with mkdocs_gen_files.open(md_path, "w") as f:
        print(f"# {name}\n", file=f)
        print(f"- **Source:** `{rel_root_dir}/{infile.name}`\n", file=f)

        if entities_ok:
            print("## Classes & Properties\n", file=f)
            print(entities_md.read_text(encoding="utf-8"), file=f)

        if metrics_ok:
            print("\n## Metrics\n", file=f)
            print(metrics_html.read_text(encoding="utf-8"), file=f)

        if report_ok:
            print("\n## QC Report\n", file=f)
            print(report_md.read_text(encoding="utf-8"), file=f)
        else:
            print("\n!!! warning \"QC report\"\n    ROBOT report could not be generated.\n", file=f)

    return md_path

def build_ontology_index(pages_with_dirs):
    index_md = Path("ontologies/index.md")
    with mkdocs_gen_files.open(index_md, "w") as f:
        print("# Ontologies\n", file=f)
        if not pages_with_dirs:
            print("_No ontologies found in configured directories._", file=f)
            return
        from collections import defaultdict
        groups = defaultdict(list)
        for md, relroot in pages_with_dirs:
            groups[relroot].append(md)
        for relroot in sorted(groups.keys()):
            print(f"## {relroot}\n", file=f)
            for md in groups[relroot]:
                print(f"- [{md.stem}]({md.name})", file=f)
            print("", file=f)

# ---------- Patterns / Process ODPs ----------
def discover_patterns():
    """
    Expected tree:
      Patterns/<Ontology>/<Requirement>/<file.ttl>
    Returns list of tuples:
      (file_path, ontology_name, requirement_name)
    """
    found = []
    if not PATTERNS_DIR.exists():
        return found
    for ont_dir in sorted([p for p in PATTERNS_DIR.iterdir() if p.is_dir()]):
        ont = ont_dir.name
        for req_dir in sorted([p for p in ont_dir.iterdir() if p.is_dir()]):
            req = req_dir.name
            for f in sorted(req_dir.glob("**/*")):
                if f.is_file() and f.suffix.lower() in PATTERN_EXTS:
                    found.append((f, ont, req))
    return found

def make_pattern_page(infile: Path, ontology: str, requirement: str):
    """
    Writes page to patterns/<ontology>/<requirement>/<name>.md
    Embeds: metrics (html), report (md), entities (md)
    """
    name = infile.stem
    pdir = ROOT / "docs" / "patterns" / ontology / requirement / name
    pdir.mkdir(parents=True, exist_ok=True)

    report_ok = entities_ok = metrics_ok = False
    try:
        report_md = robot_report(infile, pdir)
        report_ok = True
    except Exception:
        report_md = None
    try:
        entities_md = sparql_entities(infile, pdir)
        entities_ok = True
    except Exception:
        entities_md = None
    try:
        metrics_html = robot_measure(infile, pdir)
        metrics_ok = True
    except Exception:
        metrics_html = None

    md_rel = Path(f"patterns/{ontology}/{requirement}/{name}.md")
    with mkdocs_gen_files.open(md_rel, "w") as f:
        print(f"# {ontology} · {requirement} · {name}\n", file=f)
        rel_src = f"Patterns/{ontology}/{requirement}/{infile.name}"
        print(f"- **Source:** `{rel_src}`\n", file=f)

        if entities_ok:
            print("## Classes & Properties\n", file=f)
            print(entities_md.read_text(encoding="utf-8"), file=f)

        if metrics_ok:
            print("\n## Metrics\n", file=f)
            print(metrics_html.read_text(encoding="utf-8"), file=f)

        if report_ok:
            print("\n## QC Report\n", file=f)
            print(report_md.read_text(encoding="utf-8"), file=f)
        else:
            print("\n!!! warning \"QC report\"\n    ROBOT report could not be generated.\n", file=f)

    return md_rel

def build_patterns_index(pattern_pages):
    """
    Returns a dict {ontology: {requirement: [Path(md), ...]}}
    and writes ProcessODPs.md to show the grouped list.
    """
    from collections import defaultdict
    tree: dict[str, dict[str, list[Path]]] = defaultdict(lambda: defaultdict(list))
    for md, ont, req in pattern_pages:
        tree[ont][req].append(md)

    # Create a browsable index at patterns/index.md (optional)
    with mkdocs_gen_files.open(Path("patterns/index.md"), "w") as f:
        print("# Process ODPs\n", file=f)
        if not pattern_pages:
            print("_No patterns found under `Patterns/`._", file=f)
        else:
            for ont in sorted(tree.keys()):
                print(f"## {ont}\n", file=f)
                for req in sorted(tree[ont].keys()):
                    print(f"### {req}\n", file=f)
                    for md in tree[ont][req]:
                        print(f"- [{md.stem}]({md.as_posix()})", file=f)
                    print("", file=f)

    # Overwrite docs/ProcessODPs.md at build-time with the same content
    # (so your existing nav keeps working).
    with mkdocs_gen_files.open(Path("ProcessODPs.md"), "w") as f:
        print("# Process ODPs\n", file=f)
        print("Here is the list of Ontology Design Patterns (ODPs) aligned with process modeling requirements in the Materials Science and Engineering (MSE) domain.\n", file=f)
        if not pattern_pages:
            print("_No patterns found under `Patterns/`._", file=f)
        else:
            for ont in sorted(tree.keys()):
                print(f"## {ont}\n", file=f)
                for req in sorted(tree[ont].keys()):
                    print(f"### {req}\n", file=f)
                    for md in tree[ont][req]:
                        print(f"- [{md.stem}]({md.as_posix()})", file=f)
                    print("", file=f)

    return tree

# ---------- Main ----------
def main():
    # Ontologies
    onto_files = discover_ontologies()
    onto_pages = [(make_ontology_page(p, relroot), relroot) for p, relroot in onto_files]
    build_ontology_index(onto_pages)

    # Patterns
    pat_files = discover_patterns()
    pat_pages = [(make_pattern_page(p, ont, req), ont, req) for p, ont, req in pat_files]
    build_patterns_index(pat_pages)

if __name__ == "__main__":
    main()
