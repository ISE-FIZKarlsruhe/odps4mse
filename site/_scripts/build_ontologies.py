# docs/_scripts/build_ontologies.py
import os, subprocess, re, csv
from pathlib import Path
import mkdocs_gen_files

# =============== Config ===============
ROOT = Path(__file__).resolve().parents[2]

# Multiple ontology dirs (comma-separated). Defaults to "Ontologies".
ONTOLOGY_DIRS = [
    (ROOT / p.strip())
    for p in os.environ.get("ONTOLOGY_DIRS", "Ontologies").split(",")
    if p.strip()
]
ONTO_EXTS = (".owl", ".ttl", ".rdf", ".obo")

# Process ODP patterns root dir
PATTERNS_DIR = ROOT / os.environ.get("PATTERNS_DIR", "Patterns")
PATTERN_EXTS = (".ttl", ".owl", ".rdf")

# Metrics level for ROBOT measure
MEASURE_LEVEL = os.environ.get("MEASURE_LEVEL", "essential")  # essential|extended|all|*-reasoner


# =============== Utilities ===============
def run(cmd: list[str]):
    """Run a subprocess and raise if it fails."""
    subprocess.run(cmd, check=True)

def open_virtual(relpath: Path | str, mode: str = "w"):
    """
    Always open virtual files with POSIX-style paths so it works on Windows too.
    """
    if isinstance(relpath, Path):
        relpath = relpath.as_posix()  # force forward slashes
    return mkdocs_gen_files.open(relpath, mode)


def tsv_to_markdown_table(tsv_path: Path, max_rows: int | None = None) -> str:
    """Convert a TSV file to a Markdown table string."""
    if not tsv_path.exists():
        return "_No data found._"
    rows = []
    with tsv_path.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if max_rows is not None and i > max_rows:
                break
            rows.append(line.rstrip("\n").split("\t"))
    if not rows:
        return "_No data found._"
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


# helper: copy the original file next to the page for download
def copy_download(src: Path, rel_dest: Path):
    """
    Copy src bytes into the virtual docs tree at rel_dest, so users can download.
    rel_dest is a path relative to site root (e.g., ontologies/BBO/BBO.ttl).
    """
    with mkdocs_gen_files.open(rel_dest, "wb") as outf:
        outf.write(src.read_bytes())
    return rel_dest.name  # return simple name for relative link


# =============== ROBOT helpers ===============
def robot_report(infile: Path, report_rel_md_path: Path, workdir: Path) -> Path:
    """
    Run ROBOT report with --fail-on none, convert TSV -> Markdown, and
    write a dedicated report page with search excluded via front matter.
    """
    workdir.mkdir(parents=True, exist_ok=True)
    tsv = workdir / "report.tsv"

    run([
        "robot", "report",
        "-i", str(infile),
        "--fail-on", "none",           # never fail the build
        "--output", str(tsv)
    ])

    md_body = tsv_to_markdown_table(tsv, max_rows=None)
    report_md_text = f"---\nsearch:\n  exclude: true\n---\n\n{md_body}\n"

    with mkdocs_gen_files.open(report_rel_md_path, "w") as rf:
        rf.write(report_md_text)

    return report_rel_md_path


def robot_measure(infile: Path, metrics_rel_md_path: Path, workdir: Path) -> Path:
    """
    Run ROBOT measure, produce HTML, and write a dedicated metrics page
    with search excluded via front matter. Returns the page path.
    """
    workdir.mkdir(parents=True, exist_ok=True)
    html_path = workdir / "metrics.html"
    run([
        "robot", "measure",
        "-i", str(infile),
        "--metrics", MEASURE_LEVEL,
        "--format", "html",
        "-o", str(html_path),
    ])

    html = html_path.read_text(encoding="utf-8")
    metrics_page_text = f"---\nsearch:\n  exclude: true\n---\n\n{html}\n"

    with mkdocs_gen_files.open(metrics_rel_md_path, "w") as mf:
        mf.write(metrics_page_text)

    return metrics_rel_md_path


# =============== Entities extraction (searchable + aggregatable) ===============
def sparql_entities_to_tsv(infile: Path, outdir: Path) -> Path:
    """
    Run the SPARQL query and write entities.tsv with columns:
    LABEL, LOCAL, TYPE, IRI
    """
    outdir.mkdir(parents=True, exist_ok=True)
    tsv = outdir / "entities.tsv"

    query = r"""
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX owl:  <http://www.w3.org/2002/07/owl#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX oio:  <http://www.geneontology.org/formats/oboInOwl#>

SELECT
  (COALESCE(STR(?lab), STR(?alt), ?LOCAL) AS ?LABEL)
  ?LOCAL
  (COALESCE(?typeShort, "Entity") AS ?TYPE)
  (STR(?e) AS ?IRI)
WHERE {
  {
    { ?e rdfs:label ?lab } UNION { ?e skos:prefLabel ?lab }
  } UNION {
    ?e ?p ?o .
    FILTER(isIRI(?e))
  }

  OPTIONAL {
    { ?e skos:altLabel ?alt } UNION { ?e oio:hasExactSynonym ?alt }
  }

  BIND(STR(?e) AS ?s)
  BIND( REPLACE(?s, "^.*#", "") AS ?fragHash )
  BIND( REPLACE(?s, "^.*/", "") AS ?fragSlash )
  BIND( IF(CONTAINS(?s, "#"), ?fragHash, ?fragSlash) AS ?LOCAL )

  OPTIONAL { ?e rdf:type ?t . }
  BIND(
    IF(?t = owl:Class, "Class",
    IF(?t = owl:ObjectProperty, "ObjectProperty",
    IF(?t = owl:DatatypeProperty, "DatatypeProperty",
    IF(?t = owl:AnnotationProperty, "AnnotationProperty",
    IF(?t = owl:NamedIndividual, "Individual", "Entity"))))) AS ?typeShort
  )
}
GROUP BY ?e ?lab ?alt ?LOCAL ?typeShort
ORDER BY LCASE(COALESCE(STR(?lab), ?LOCAL))
"""
    qfile = outdir / "entities.sparql"
    qfile.write_text(query, encoding="utf-8")

    run([
        "robot","query",
        "-i", str(infile),
        "--query", f"{qfile}=tsv",
        str(tsv)
    ])
    return tsv


def entities_markdown_list_from_tsv(tsv: Path) -> Path:
    """
    Render the TSV as a bulleted list with hidden tokens to boost search.
    Returns path to entities.md placed next to TSV.
    """
    md = tsv.with_name("entities.md")

    def tokenize_variants(text: str) -> set[str]:
        if not text:
            return set()
        spaced = re.sub(r'(?<!^)(?=[A-Z][a-z])', ' ', text)
        spaced = spaced.replace('_', ' ').replace('-', ' ')
        return {
            text,
            text.lower(),
            spaced,
            spaced.lower(),
            text.replace('_', ' ').replace('-', ' '),
        }

    lines = []
    with tsv.open("r", encoding="utf-8") as f:
        rows = [line.rstrip("\n").split("\t") for line in f]
    if rows:
        header = rows[0]
        idx = {h:i for i,h in enumerate(header)}
        for r in rows[1:]:
            label = r[idx.get("LABEL", 0)] if len(r) > idx.get("LABEL", 0) else ""
            local = r[idx.get("LOCAL", 1)] if len(r) > idx.get("LOCAL", 1) else ""
            typ   = r[idx.get("TYPE", 2)]  if len(r) > idx.get("TYPE", 2)  else ""
            iri   = r[idx.get("IRI", 3)]   if len(r) > idx.get("IRI", 3)   else ""
            tokens = " ".join(sorted(tokenize_variants(label) | tokenize_variants(local) | tokenize_variants(iri)))
            lines.append(
                f"- **{label or local}** (*{typ or 'Entity'}*) — `{local}` — <{iri}>"
                f"\n  <span class='search-tokens' style='display:none'>{tokens}</span>"
            )
    md.write_text("\n".join(lines) if lines else "_No entities found._", encoding="utf-8")
    return md


def read_entities_rows(tsv: Path):
    """
    Yield dict rows {'LABEL','LOCAL','TYPE','IRI'} from entities.tsv.
    """
    if not tsv.exists():
        return []
    rows_out = []
    with tsv.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            rows_out.append({
                "LABEL": row.get("LABEL",""),
                "LOCAL": row.get("LOCAL",""),
                "TYPE":  row.get("TYPE",""),
                "IRI":   row.get("IRI",""),
            })
    return rows_out


# =============== Ontologies ===============
def discover_ontologies():
    found = []
    for d in ONTOLOGY_DIRS:
        if not d.exists():
            continue
        rel = str(d.relative_to(ROOT))
        for p in sorted(d.rglob("*")):
            if p.is_file() and p.suffix.lower() in ONTO_EXTS:
                found.append((p, rel))
    return found


def make_ontology_page(infile: Path, rel_root_dir: str, all_terms_accum: list) -> Path:
    """
    Build page: ontologies/<name>.md
    Reports: ontologies/<name>/report.md (search-excluded)
    Metrics: ontologies/<name>/metrics.md (search-excluded)
    Accumulate terms into all_terms_accum with links back to this page.
    """
    name = infile.stem
    workdir = ROOT / "docs" / "ontologies" / name
    workdir.mkdir(parents=True, exist_ok=True)

    report_ok = entities_ok = metrics_ok = False
    report_rel_md = Path(f"ontologies/{name}/report.md")
    metrics_rel_md = Path(f"ontologies/{name}/metrics.md")
    entities_tsv = None
    entities_md = None

    # Copy original file for download
    download_name = copy_download(infile, Path(f"ontologies/{name}/{infile.name}"))

    try:
        robot_report(infile, report_rel_md, workdir); report_ok = True
    except Exception:
        pass
    try:
        entities_tsv = sparql_entities_to_tsv(infile, workdir)
        entities_md = entities_markdown_list_from_tsv(entities_tsv)
        entities_ok = True
    except Exception:
        pass
    try:
        robot_measure(infile, metrics_rel_md, workdir); metrics_ok = True
    except Exception:
        pass

    # Accumulate terms (for the global All Terms page)
    if entities_tsv and entities_tsv.exists():
        for row in read_entities_rows(entities_tsv):
            all_terms_accum.append({
                "LABEL": row["LABEL"] or row["LOCAL"],
                "LOCAL": row["LOCAL"],
                "TYPE":  row["TYPE"] or "Entity",
                "IRI":   row["IRI"],
                "SOURCE_KIND": "Ontology",
                "SOURCE_NAME": name,
                "LINK": f"ontologies/{name}/",   # use directory URL
            })

    page_rel = Path(f"ontologies/{name}.md")
    with mkdocs_gen_files.open(page_rel, "w") as f:
        print(f"# {name}\n", file=f)
        print(f"- **Source:** `{rel_root_dir}/{infile.name}`  ·  **[Download]({download_name})**\n", file=f)

        if entities_ok and entities_md:
            print("## Classes & Properties\n", file=f)
            print(entities_md.read_text(encoding="utf-8"), file=f)

        if metrics_ok:
            print("\n## Metrics\n", file=f)
            print("See metrics (not indexed by search): [metrics](metrics/)", file=f)

        if report_ok:
            print("\n## QC Report\n", file=f)
            print("See the full report (not indexed by search): [report](report/)", file=f)
        else:
            print("\n!!! warning \"QC report\"\n    ROBOT report could not be generated.\n", file=f)

    return page_rel


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


# =============== Patterns (Process ODPs) ===============
def discover_patterns():
    """
    Expected tree:
      Patterns/<Ontology>/<Requirement>/<file.ttl|owl|rdf>
    Returns [(file_path, ontology_name, requirement_name)]
    """
    found = []
    if not PATTERNS_DIR.exists():
        return found
    for ont_dir in sorted([p for p in PATTERNS_DIR.iterdir() if p.is_dir()]):
        ont = ont_dir.name
        for req_dir in sorted([p for p in ont_dir.iterdir() if p.is_dir()]):
            req = req_dir.name
            for f in sorted(req_dir.rglob("*")):
                if f.is_file() and f.suffix.lower() in PATTERN_EXTS:
                    found.append((f, ont, req))
    return found


def make_pattern_page(infile: Path, ontology: str, requirement: str, all_terms_accum: list) -> Path:
    """
    Page: patterns/<Ontology>/<Requirement>/<Pattern>.md
    Report: patterns/<Ontology>/<Requirement>/<Pattern>/report.md (search-excluded)
    Metrics: patterns/<Ontology>/<Requirement>/<Pattern>/metrics.md (search-excluded)
    Accumulate terms into all_terms_accum with links back to this page.
    """
    name = infile.stem
    workdir = ROOT / "docs" / "patterns" / ontology / requirement / name
    workdir.mkdir(parents=True, exist_ok=True)

    report_ok = entities_ok = metrics_ok = False
    report_rel_md = Path(f"patterns/{ontology}/{requirement}/{name}/report.md")
    metrics_rel_md = Path(f"patterns/{ontology}/{requirement}/{name}/metrics.md")
    entities_tsv = None
    entities_md = None

    # Copy original file for download
    download_name = copy_download(infile, Path(f"patterns/{ontology}/{requirement}/{name}/{infile.name}"))

    try:
        robot_report(infile, report_rel_md, workdir); report_ok = True
    except Exception:
        pass
    try:
        entities_tsv = sparql_entities_to_tsv(infile, workdir)
        entities_md = entities_markdown_list_from_tsv(entities_tsv)
        entities_ok = True
    except Exception:
        pass
    try:
        robot_measure(infile, metrics_rel_md, workdir); metrics_ok = True
    except Exception:
        pass

    # Accumulate terms (for the global All Terms page)
    if entities_tsv and entities_tsv.exists():
        for row in read_entities_rows(entities_tsv):
            all_terms_accum.append({
                "LABEL": row["LABEL"] or row["LOCAL"],
                "LOCAL": row["LOCAL"],
                "TYPE":  row["TYPE"] or "Entity",
                "IRI":   row["IRI"],
                "SOURCE_KIND": "Pattern",
                "SOURCE_NAME": f"{ontology} / {requirement} / {name}",
                "LINK": f"patterns/{ontology}/{requirement}/{name}/",  # directory URL
            })

    page_rel = Path(f"patterns/{ontology}/{requirement}/{name}.md")
    with mkdocs_gen_files.open(page_rel, "w") as f:
        print(f"# {ontology} · {requirement} · {name}\n", file=f)
        rel_src = f"Patterns/{ontology}/{requirement}/{infile.name}"
        print(f"- **Source:** `{rel_src}`  ·  **[Download]({download_name})**\n", file=f)

        if entities_ok and entities_md:
            print("## Classes & Properties\n", file=f)
            print(entities_md.read_text(encoding="utf-8"), file=f)

        if metrics_ok:
            print("\n## Metrics\n", file=f)
            print("See metrics (not indexed by search): [metrics](metrics/)", file=f)

        if report_ok:
            print("\n## QC Report\n", file=f)
            print("See the full report (not indexed by search): [report](report/)", file=f)
        else:
            print("\n!!! warning \"QC report\"\n    ROBOT report could not be generated.\n", file=f)

    return page_rel


def build_patterns_index(pattern_pages):
    """
    Build ProcessODPs.md and patterns/index.md with grouped links.
    """
    from collections import defaultdict
    tree: dict[str, dict[str, list[Path]]] = defaultdict(lambda: defaultdict(list))
    for md, ont, req in pattern_pages:
        tree[ont][req].append(md)

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


# =============== Global All Terms page ===============
def build_all_terms_page(all_terms: list):
    """
    Write terms/index.md (All Terms) and terms/all-terms.csv
    Columns: Label | Local | Type | IRI | Source | Link
    """
    # Sort by Label (case-insensitive)
    all_terms_sorted = sorted(all_terms, key=lambda r: (r.get("LABEL","") or "").lower())

    # Write CSV for download
    csv_rel = Path("terms/all-terms.csv")
    with mkdocs_gen_files.open(csv_rel, "w") as cf:
        writer = csv.writer(cf)
        writer.writerow(["LABEL", "LOCAL", "TYPE", "IRI", "SOURCE", "LINK"])
        for r in all_terms_sorted:
            writer.writerow([
                r.get("LABEL",""),
                r.get("LOCAL",""),
                r.get("TYPE",""),
                r.get("IRI",""),
                f"{r.get('SOURCE_KIND','')} : {r.get('SOURCE_NAME','')}",
                r.get("LINK",""),
            ])

    # Write Markdown table (large pages are okay; Material search handles it)
    md_rel = Path("terms/index.md")
    with mkdocs_gen_files.open(md_rel, "w") as f:
        print("# All Terms\n", file=f)
        print(f"[Download CSV]({csv_rel.name})\n", file=f)
        print("| Label | Local | Type | IRI | Source | Link |", file=f)
        print("| --- | --- | --- | --- | --- | --- |", file=f)
        for r in all_terms_sorted:
            label = r.get("LABEL","").replace("|","\\|")
            local = r.get("LOCAL","").replace("|","\\|")
            typ   = r.get("TYPE","").replace("|","\\|")
            iri   = r.get("IRI","").replace("|","\\|")
            src   = f"{r.get('SOURCE_KIND','')} : {r.get('SOURCE_NAME','')}".replace("|","\\|")
            link  = r.get("LINK","")
            print(f"| {label} | `{local}` | {typ} | <{iri}> | {src} | [open]({link}) |", file=f)


# =============== Main ===============
def main():
    # Accumulator for all terms across ontologies and patterns
    all_terms = []

    # Ontologies
    onto_files = discover_ontologies()
    onto_pages = [(make_ontology_page(p, relroot, all_terms), relroot) for p, relroot in onto_files]
    build_ontology_index(onto_pages)

    # Patterns
    pat_files = discover_patterns()
    pat_pages = [(make_pattern_page(p, ont, req, all_terms), ont, req) for p, ont, req in pat_files]
    build_patterns_index(pat_pages)

    # All Terms
    build_all_terms_page(all_terms)


if __name__ == "__main__":
    main()
