# docs/_scripts/build_ontologies.py
import os, re, csv, subprocess, sys, json, shutil
from pathlib import Path
from typing import Optional, Dict, Any, List
import mkdocs_gen_files

# ================= Config =================
ROOT = Path(__file__).resolve().parents[2]

# Comma-separated ontology roots (relative to repo or absolute)
ONTOLOGY_DIRS: List[Path] = []
for p in os.environ.get("ONTOLOGY_DIRS", "Ontologies").split(","):
    p = p.strip()
    if not p:
        continue
    P = Path(p)
    if not P.is_absolute():
        P = ROOT / P
    ONTOLOGY_DIRS.append(P)

ONTO_EXTS = (".owl", ".ttl", ".rdf", ".obo")

PATTERNS_DIR = Path(os.environ.get("PATTERNS_DIR", ROOT / "Patterns"))
if not PATTERNS_DIR.is_absolute():
    PATTERNS_DIR = ROOT / PATTERNS_DIR

PATTERN_EXTS = (".ttl", ".owl", ".rdf", ".obo")  # allow .obo too

MEASURE_LEVEL = os.environ.get("MEASURE_LEVEL", "essential")
ROBOT_CATALOG = os.environ.get("ROBOT_CATALOG", "catalog-v001.xml")
EXTRACT_WITH_RDFLIB_ONLY = os.environ.get("EXTRACT_WITH_RDFLIB_ONLY", "0") == "1"

def log(msg: str):
    print(f"[gen] {msg}", file=sys.stdout, flush=True)

def run(cmd: list[str], check: bool = True):
    log("CMD$ " + " ".join(cmd))
    subprocess.run(cmd, check=check)

def open_virtual(relpath: Path | str, mode: str = "w"):
    if isinstance(relpath, Path):
        relpath = relpath.as_posix()
    return mkdocs_gen_files.open(relpath, mode)

def tsv_to_markdown_table(tsv_path: Path, max_rows: int | None = None) -> str:
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

def copy_download(src: Path, rel_dest: Path):
    with open_virtual(rel_dest, "wb") as outf:
        outf.write(src.read_bytes())
    return rel_dest.name

# ================= ROBOT helpers =================
def _robot_base_cmd():
    cmd = ["robot"]
    cat = ROOT / ROBOT_CATALOG
    if ROBOT_CATALOG and cat.exists():
        cmd += ["--catalog", str(cat)]
        log(f"Using ROBOT catalog: {cat}")
    return cmd

def robot_materialize_imports(infile: Path, workdir: Path) -> Path:
    """
    Try to produce a merged file with imports included.
    On success returns merged path, else returns the original infile.
    """
    workdir.mkdir(parents=True, exist_ok=True)
    merged = workdir / "merged.owl"
    try:
        cmd = _robot_base_cmd() + [
            "merge", "-i", str(infile),
            "--include-annotations", "true",
            "-o", str(merged),
        ]
        run(cmd)
        if merged.exists() and merged.stat().st_size > 0:
            log(f"Materialized imports for {infile.name} -> {merged.name} ({merged.stat().st_size} bytes)")
            return merged
    except Exception as e:
        log(f"ROBOT merge failed for {infile.name}: {e}")
    return infile

def robot_convert_to_ttl(infile: Path, outdir: Path) -> Optional[Path]:
    """
    For .obo or other tricky formats, convert to TTL so rdflib can parse reliably.
    """
    outdir.mkdir(parents=True, exist_ok=True)
    ttl = outdir / (infile.stem + ".ttl")
    try:
        cmd = _robot_base_cmd() + ["convert", "-i", str(infile), "-o", str(ttl)]
        run(cmd)
        if ttl.exists() and ttl.stat().st_size > 0:
            log(f"Converted {infile.name} -> {ttl.name}")
            return ttl
    except Exception as e:
        log(f"ROBOT convert failed for {infile.name}: {e}")
    return None

def robot_report(infile: Path, report_rel_md_path: Path, workdir: Path) -> Path:
    workdir.mkdir(parents=True, exist_ok=True)
    tsv = workdir / "report.tsv"
    cmd = _robot_base_cmd() + ["report", "-i", str(infile), "--fail-on", "none", "--output", str(tsv)]
    run(cmd)
    md_body = tsv_to_markdown_table(tsv, max_rows=None)
    report_md_text = f"---\nsearch:\n  exclude: true\n---\n\n{md_body}\n"
    with open_virtual(report_rel_md_path, "w") as rf:
        rf.write(report_md_text)
    return report_rel_md_path

def robot_measure(infile: Path, metrics_rel_md_path: Path, workdir: Path) -> Path:
    workdir.mkdir(parents=True, exist_ok=True)
    html_path = workdir / "metrics.html"
    cmd = _robot_base_cmd() + ["measure", "-i", str(infile), "--metrics", MEASURE_LEVEL, "--format", "html", "-o", str(html_path)]
    run(cmd)
    html = html_path.read_text(encoding="utf-8")
    metrics_page_text = f"---\nsearch:\n  exclude: true\n---\n\n{html}\n"
    with open_virtual(metrics_rel_md_path, "w") as mf:
        mf.write(metrics_page_text)
    return metrics_rel_md_path

# ================= SPARQL queries =================
RICH_QUERY = r"""
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX owl:  <http://www.w3.org/2002/07/owl#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX oio:  <http://www.geneontology.org/formats/oboInOwl#>
SELECT
  (COALESCE(STR(?lab), STR(?alt1), ?LOCAL) AS ?LABEL)
  ?LOCAL
  (COALESCE(?typeShort, "Entity") AS ?TYPE)
  (STR(?e) AS ?IRI)
  (GROUP_CONCAT(DISTINCT STR(?alt2); separator=" | ") AS ?ALT_LABELS)
  (GROUP_CONCAT(DISTINCT STR(?syn);  separator=" | ") AS ?SYNONYMS)
  (SAMPLE(STR(?com)) AS ?COMMENT)
WHERE {
  {
    { ?e rdfs:label ?lab } UNION { ?e skos:prefLabel ?lab }
  } UNION {
    ?e ?p ?o .
    FILTER(isIRI(?e))
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
  OPTIONAL { { ?e skos:altLabel ?alt2 } UNION { ?e oio:hasExactSynonym ?alt2 } }
  OPTIONAL { { ?e skos:altLabel ?alt1 } UNION { ?e oio:hasExactSynonym ?alt1 } }
  OPTIONAL {
    { ?e oio:hasRelatedSynonym ?syn } UNION
    { ?e oio:hasBroadSynonym   ?syn } UNION
    { ?e oio:hasNarrowSynonym  ?syn } UNION
    { ?e oio:hasExactSynonym   ?syn }
  }
  OPTIONAL { ?e rdfs:comment ?com }
}
GROUP BY ?e ?lab ?LOCAL ?typeShort
ORDER BY LCASE(COALESCE(STR(?lab), ?LOCAL))
"""

FALLBACK_QUERY = r"""
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX owl:  <http://www.w3.org/2002/07/owl#>
SELECT
  (COALESCE(STR(?lab), ?LOCAL) AS ?LABEL)
  ?LOCAL
  (COALESCE(?typeShort, "Entity") AS ?TYPE)
  (STR(?e) AS ?IRI)
  ("" AS ?ALT_LABELS)
  ("" AS ?SYNONYMS)
  (SAMPLE(STR(?com)) AS ?COMMENT)
WHERE {
  ?e ?p ?o .
  FILTER(isIRI(?e))
  OPTIONAL { ?e rdfs:label ?lab . }
  OPTIONAL { ?e rdfs:comment ?com . }
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
GROUP BY ?e ?lab ?LOCAL ?typeShort
ORDER BY LCASE(COALESCE(STR(?lab), ?LOCAL))
"""

def sparql_run_to_tsv(infile: Path, outdir: Path, sparql_text: str, tsv_out: Path) -> int:
    qfile = outdir / "entities.sparql"
    qfile.write_text(sparql_text, encoding="utf-8")
    try:
        cmd = _robot_base_cmd() + ["query", "-i", str(infile), "--query", f"{qfile}=tsv", str(tsv_out)]
        run(cmd)
    except Exception as e:
        log(f"ROBOT query failed: {e}")
        return -1
    try:
        with tsv_out.open("r", encoding="utf-8") as f:
            lines = f.readlines()
        return max(0, len(lines) - 1)
    except Exception as e:
        log(f"Failed reading TSV {tsv_out}: {e}")
        return -1

# ================= rdflib fallback =================
def rdflib_extract_to_tsv(infile: Path, tsv_out: Path) -> int:
    """
    Parse infile with rdflib and write entities.tsv with columns:
    LABEL, LOCAL, TYPE, IRI, ALT_LABELS, SYNONYMS, COMMENT
    Returns row count.
    """
    from rdflib import Graph, URIRef, RDF, RDFS, Namespace

    SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
    OIO  = Namespace("http://www.geneontology.org/formats/oboInOwl#")
    OWL  = Namespace("http://www.w3.org/2002/07/owl#")

    g = Graph()
    # Try to sniff format. If rdfxml fails on .owl, let rdflib guess.
    try:
        g.parse(infile.as_posix())
    except Exception as e:
        log(f"rdflib parse failed for {infile.name}: {e}")
        return 0

    def local_name(iri: str) -> str:
        if "#" in iri:
            return iri.rsplit("#", 1)[1]
        return iri.rstrip("/").rsplit("/", 1)[-1] if "/" in iri else iri

    subjects = set(s for s in g.subjects() if isinstance(s, URIRef))
    labeled  = set(s for s,_ in g.subject_objects(RDFS.label) if isinstance(s, URIRef))
    entities = subjects | labeled

    rows: List[Dict[str, Any]] = []
    for e in entities:
        iri = str(e)
        labels = {str(o) for o in g.objects(e, RDFS.label)} | {str(o) for o in g.objects(e, SKOS.prefLabel)}
        label = next(iter(labels), "")
        alts = {str(o) for o in g.objects(e, SKOS.altLabel)} | {str(o) for o in g.objects(e, OIO.hasExactSynonym)}
        syns = (
            {str(o) for o in g.objects(e, OIO.hasRelatedSynonym)} |
            {str(o) for o in g.objects(e, OIO.hasBroadSynonym)}   |
            {str(o) for o in g.objects(e, OIO.hasNarrowSynonym)}  |
            {str(o) for o in g.objects(e, OIO.hasExactSynonym)}
        )
        comments = [str(o) for o in g.objects(e, RDFS.comment)]
        comment = comments[0] if comments else ""
        types = list(g.objects(e, RDF.type))
        typ = ""
        for t in types:
            ts = str(t)
            if ts == str(OWL.Class):              typ = "Class"; break
            if ts == str(OWL.ObjectProperty):     typ = "ObjectProperty"; break
            if ts == str(OWL.DatatypeProperty):   typ = "DatatypeProperty"; break
            if ts == str(OWL.AnnotationProperty): typ = "AnnotationProperty"; break
            if ts == str(OWL.NamedIndividual):    typ = "Individual"; break
        if not typ:
            typ = "Entity"

        rows.append({
            "LABEL": label or local_name(iri),
            "LOCAL": local_name(iri),
            "TYPE":  typ,
            "IRI":   iri,
            "ALT_LABELS": " | ".join(sorted(alts)) if alts else "",
            "SYNONYMS":   " | ".join(sorted(syns)) if syns else "",
            "COMMENT":    comment,
        })

    with tsv_out.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["LABEL","LOCAL","TYPE","IRI","ALT_LABELS","SYNONYMS","COMMENT"])
        for r in rows:
            w.writerow([r["LABEL"], r["LOCAL"], r["TYPE"], r["IRI"], r["ALT_LABELS"], r["SYNONYMS"], r["COMMENT"]])

    log(f"rdflib extracted {len(rows)} rows from {infile.name}")
    return len(rows)

# ================= Extraction orchestrator =================
def entities_to_tsv_with_fallbacks(infile: Path, workdir: Path, allow_robot: bool = True) -> Optional[Path]:
    """
    Returns path to entities.tsv or None.
    Strategy:
      1) If allow_robot: ROBOT merge (imports) -> SPARQL rich -> SPARQL fallback
      2) rdflib on materialized file
      3) If still 0 and suffix .obo, ROBOT convert -> rdflib on TTL
    """
    workdir.mkdir(parents=True, exist_ok=True)
    tsv = workdir / "entities.tsv"

    # Step 0: maybe bypass ROBOT entirely (debug mode)
    if not allow_robot:
        log(f"EXTRACT_WITH_RDFLIB_ONLY=1 — skipping ROBOT for {infile.name}")
        mat = infile
        n3 = rdflib_extract_to_tsv(mat, tsv)
        return tsv if n3 > 0 else None

    # Step 1: materialize imports
    mat = robot_materialize_imports(infile, workdir)

    # Step 2: SPARQL rich
    n = sparql_run_to_tsv(mat, workdir, RICH_QUERY, tsv)
    if n > 0:
        log(f"ROBOT rich query rows for {infile.name}: {n}")
        return tsv

    # Step 3: SPARQL fallback
    log(f"No rows from rich query for {infile.name}; trying ROBOT fallback query…")
    n2 = sparql_run_to_tsv(mat, workdir, FALLBACK_QUERY, tsv)
    if n2 > 0:
        log(f"ROBOT fallback query rows for {infile.name}: {n2}")
        return tsv

    # Step 4: rdflib on materialized/original
    log(f"ROBOT produced no rows for {infile.name}; using rdflib…")
    n3 = rdflib_extract_to_tsv(mat, tsv)
    if n3 > 0:
        return tsv

    # Step 5: If OBO, convert to TTL then rdflib
    if infile.suffix.lower() == ".obo":
        log(f"Trying ROBOT convert for OBO: {infile.name}")
        ttl = robot_convert_to_ttl(infile, workdir)
        if ttl:
            n4 = rdflib_extract_to_tsv(ttl, tsv)
            if n4 > 0:
                return tsv

    log(f"FAILED to extract entities for {infile.name}")
    return None

# ================= Renderers =================
def entities_markdown_list_from_tsv(tsv: Path) -> Path:
    md = tsv.with_name("entities.md")
    def tokenize_variants(text: str) -> set[str]:
        if not text:
            return set()
        spaced = re.sub(r'(?<!^)(?=[A-Z][a-z])', ' ', text)
        spaced = spaced.replace('_', ' ').replace('-', ' ')
        return {text, text.lower(), spaced, spaced.lower(), text.replace('_',' ').replace('-',' ')}
    rows = []
    try:
        with tsv.open("r", encoding="utf-8") as f:
            rows = [line.rstrip("\n").split("\t") for line in f]
    except Exception as e:
        log(f"could not read TSV {tsv}: {e}")
    lines = []
    if rows:
        header = rows[0]
        idx = {h:i for i,h in enumerate(header)}
        for r in rows[1:]:
            def col(name, default=""):
                i = idx.get(name)
                return r[i] if i is not None and i < len(r) else default
            label = col("LABEL"); local = col("LOCAL"); typ = col("TYPE"); iri = col("IRI")
            alt = col("ALT_LABELS"); syn = col("SYNONYMS"); comment = col("COMMENT")
            tokens = " ".join(sorted(
                tokenize_variants(label) | tokenize_variants(local) | tokenize_variants(iri) |
                tokenize_variants(alt)   | tokenize_variants(syn)
            ))
            extras = []
            if alt: extras.append(f"_alt:_ {alt}")
            if syn: extras.append(f"_syn:_ {syn}")
            if comment: extras.append(f"_comment:_ {comment}")
            meta = (" — " + " · ".join(extras)) if extras else ""
            lines.append(
                f"- **{label or local or iri}** (*{typ or 'Entity'}*) — `{local}` — <{iri}>{meta}"
                f"\n  <span class='search-tokens' style='display:none'>{tokens}</span>"
            )
    md.write_text("\n".join(lines) if lines else "_No entities found._", encoding="utf-8")
    return md

def read_entities_rows(tsv: Path):
    if not tsv or not tsv.exists():
        return []
    rows_out = []
    try:
        with tsv.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                rows_out.append({
                    "LABEL": row.get("LABEL",""),
                    "LOCAL": row.get("LOCAL",""),
                    "TYPE":  row.get("TYPE",""),
                    "IRI":   row.get("IRI",""),
                    "ALT_LABELS": row.get("ALT_LABELS",""),
                    "SYNONYMS":   row.get("SYNONYMS",""),
                    "COMMENT":    row.get("COMMENT",""),
                })
    except Exception as e:
        log(f"DictReader failed for {tsv}: {e}")
    return rows_out

def _collect_page_tokens_from_tsv(tsv: Optional[Path], max_terms: int = 4000) -> str:
    if not tsv or not tsv.exists():
        return ""
    tokens = []
    try:
        with tsv.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                for text in [row.get("LABEL",""), row.get("LOCAL",""), row.get("IRI",""),
                             row.get("ALT_LABELS",""), row.get("SYNONYMS","")]:
                    if not text: continue
                    t = re.sub(r'(?<!^)(?=[A-Z][a-z])', ' ', text)
                    t = t.replace('_',' ').replace('-',' ')
                    tokens.extend(t.split())
                if len(tokens) > max_terms: break
    except Exception:
        pass
    seen = set(); out = []
    for t in tokens:
        tl = t.lower()
        if tl in seen: continue
        seen.add(tl); out.append(tl)
        if len(out) >= max_terms: break
    return " ".join(out)

# ================= Discovery =================
def discover_ontologies():
    found = []
    log(f"Configured ontology roots: {', '.join(str(p) for p in ONTOLOGY_DIRS)}")
    for d in ONTOLOGY_DIRS:
        if not d.exists():
            log(f"[WARN] Ontology dir missing (skipped): {d}")
            continue
        cnt = 0
        for p in sorted(d.rglob("*")):
            if p.is_file() and p.suffix.lower() in ONTO_EXTS:
                found.append((p, str(d.relative_to(ROOT))))
                cnt += 1
        log(f"Scanned {d} -> {cnt} files")
    log(f"TOTAL ontology files found: {len(found)}")
    return found

def discover_patterns():
    found = []
    if not PATTERNS_DIR.exists():
        log(f"[WARN] Patterns dir missing (skipped): {PATTERNS_DIR}")
        return found
    cnt = 0
    for ont_dir in sorted([p for p in PATTERNS_DIR.iterdir() if p.is_dir()]):
        ont = ont_dir.name
        for req_dir in sorted([p for p in ont_dir.iterdir() if p.is_dir()]):
            req = req_dir.name
            for f in sorted(req_dir.rglob("*")):
                if f.is_file() and f.suffix.lower() in PATTERN_EXTS:
                    found.append((f, ont, req))
                    cnt += 1
    log(f"Scanned Patterns -> {cnt} files; total tuples: {len(found)}")
    return found

# ================= Page builders =================
def make_ontology_page(infile: Path, rel_root_dir: str, all_terms_accum: list) -> Path:
    name = infile.stem
    workdir = ROOT / "docs" / "ontologies" / name
    workdir.mkdir(parents=True, exist_ok=True)

    report_ok = entities_ok = metrics_ok = False
    report_rel_md = Path(f"ontologies/{name}/report.md")
    metrics_rel_md = Path(f"ontologies/{name}/metrics.md")
    entities_tsv = None
    entities_md = None

    download_name = copy_download(infile, Path(f"ontologies/{name}/{infile.name}"))

    # Imports closure (only once)
    material = infile
    if not EXTRACT_WITH_RDFLIB_ONLY:
        material = robot_materialize_imports(infile, workdir)

    try:
        if not EXTRACT_WITH_RDFLIB_ONLY:
            robot_report(material, report_rel_md, workdir); report_ok = True
    except Exception as e:
        log(f"Report failed for {infile.name}: {e}")

    try:
        entities_tsv = entities_to_tsv_with_fallbacks(material, workdir, allow_robot=(not EXTRACT_WITH_RDFLIB_ONLY))
        if entities_tsv:
            entities_md = entities_markdown_list_from_tsv(entities_tsv)
            entities_ok = True
    except Exception as e:
        log(f"Entities failed for {infile.name}: {e}")

    try:
        if not EXTRACT_WITH_RDFLIB_ONLY:
            robot_measure(material, metrics_rel_md, workdir); metrics_ok = True
    except Exception as e:
        log(f"Measure failed for {infile.name}: {e}")

    rows_added = 0
    if entities_tsv:
        for row in read_entities_rows(entities_tsv):
            all_terms_accum.append({
                "LABEL": row["LABEL"] or row["LOCAL"] or row["IRI"],
                "LOCAL": row["LOCAL"],
                "TYPE":  row["TYPE"] or "Entity",
                "IRI":   row["IRI"],
                "ALT_LABELS": row["ALT_LABELS"],
                "SYNONYMS":   row["SYNONYMS"],
                "COMMENT":    row["COMMENT"],
                "SOURCE_KIND": "Ontology",
                "SOURCE_NAME": name,
                "LINK": f"ontologies/{name}/",
            })
            rows_added += 1
    log(f"[{name}] entities rows added = {rows_added}")

    page_tokens = _collect_page_tokens_from_tsv(entities_tsv) if entities_tsv else ""

    page_rel = Path(f"ontologies/{name}.md")
    with open_virtual(page_rel, "w") as f:
        print(f"# {name}\n", file=f)
        print(f"- **Source:** `{rel_root_dir}/{infile.name}`  ·  **[Download]({download_name})**\n", file=f)
        if page_tokens:
            print(f"<span class='search-tokens' style='display:none'>{page_tokens}</span>\n", file=f)
        # Ontoink visualization for TTL ontologies
        if infile.suffix.lower() == ".ttl":
            print("## Visualization\n", file=f)
            print("```ontoink", file=f)
            print(f"source: {rel_root_dir}/{infile.name}", file=f)
            print("```\n", file=f)
        if entities_ok and entities_md:
            print("## Classes & Properties\n", file=f)
            print("<div data-search-exclude>", file=f)
            print(entities_md.read_text(encoding='utf-8'), file=f)
            print("</div>", file=f)
        if metrics_ok:
            print("\n## Metrics\n", file=f)
            print("See metrics (not indexed by search): [metrics](metrics/)", file=f)
        if report_ok:
            print("\n## QC Report\n", file=f)
            print("See the full report (not indexed by search): [report](report/)", file=f)
        elif not EXTRACT_WITH_RDFLIB_ONLY:
            print("\n!!! warning \"QC report\"\n    ROBOT report could not be generated.\n", file=f)
    return page_rel

def build_ontology_index(pages_with_dirs):
    index_md = Path("ontologies/index.md")
    with open_virtual(index_md, "w") as f:
        print("# Ontologies\n", file=f)
        if not pages_with_dirs:
            print("_No ontologies found in configured directories._", file=f); return
        from collections import defaultdict
        groups = defaultdict(list)
        for md, relroot in pages_with_dirs:
            groups[relroot].append(md)
        for relroot in sorted(groups.keys()):
            print(f"## {relroot}\n", file=f)
            for md in groups[relroot]:
                print(f"- [{md.stem}]({md.name})", file=f)
            print("", file=f)

def make_pattern_page(infile: Path, ontology: str, requirement: str, all_terms_accum: list) -> Path:
    name = infile.stem
    workdir = ROOT / "docs" / "patterns" / ontology / requirement / name
    workdir.mkdir(parents=True, exist_ok=True)

    report_ok = entities_ok = metrics_ok = False
    report_rel_md = Path(f"patterns/{ontology}/{requirement}/{name}/report.md")
    metrics_rel_md = Path(f"patterns/{ontology}/{requirement}/{name}/metrics.md")
    entities_tsv = None
    entities_md = None

    download_name = copy_download(infile, Path(f"patterns/{ontology}/{requirement}/{name}/{infile.name}"))

    material = infile
    if not EXTRACT_WITH_RDFLIB_ONLY:
        material = robot_materialize_imports(infile, workdir)

    try:
        if not EXTRACT_WITH_RDFLIB_ONLY:
            robot_report(material, report_rel_md, workdir); report_ok = True
    except Exception as e:
        log(f"Report failed for {infile.name}: {e}")

    try:
        entities_tsv = entities_to_tsv_with_fallbacks(material, workdir, allow_robot=(not EXTRACT_WITH_RDFLIB_ONLY))
        if entities_tsv:
            entities_md = entities_markdown_list_from_tsv(entities_tsv)
            entities_ok = True
    except Exception as e:
        log(f"Entities failed for {infile.name}: {e}")

    try:
        if not EXTRACT_WITH_RDFLIB_ONLY:
            robot_measure(material, metrics_rel_md, workdir); metrics_ok = True
    except Exception as e:
        log(f"Measure failed for {infile.name}: {e}")

    rows_added = 0
    if entities_tsv:
        for row in read_entities_rows(entities_tsv):
            all_terms_accum.append({
                "LABEL": row["LABEL"] or row["LOCAL"] or row["IRI"],
                "LOCAL": row["LOCAL"],
                "TYPE":  row["TYPE"] or "Entity",
                "IRI":   row["IRI"],
                "ALT_LABELS": row["ALT_LABELS"],
                "SYNONYMS":   row["SYNONYMS"],
                "COMMENT":    row["COMMENT"],
                "SOURCE_KIND": "Pattern",
                "SOURCE_NAME": f"{ontology} / {requirement} / {name}",
                "LINK": f"patterns/{ontology}/{requirement}/{name}/",
            })
            rows_added += 1
    log(f"[{ontology}/{requirement}/{name}] entities rows added = {rows_added}")

    page_tokens = _collect_page_tokens_from_tsv(entities_tsv) if entities_tsv else ""

    page_rel = Path(f"patterns/{ontology}/{requirement}/{name}.md")
    with open_virtual(page_rel, "w") as f:
        print(f"# {ontology} · {requirement} · {name}\n", file=f)
        rel_src = f"Patterns/{ontology}/{requirement}/{infile.name}"
        print(f"- **Source:** `{rel_src}`  ·  **[Download]({download_name})**\n", file=f)
        if page_tokens:
            print(f"<span class='search-tokens' style='display:none'>{page_tokens}</span>\n", file=f)
        # Ontoink visualization for TTL patterns
        if infile.suffix.lower() == ".ttl":
            print("## Visualization\n", file=f)
            print("```ontoink", file=f)
            print(f"source: {rel_src}", file=f)
            print("```\n", file=f)
        if entities_ok and entities_md:
            print("## Classes & Properties\n", file=f)
            print("<div data-search-exclude>", file=f)
            print(entities_md.read_text(encoding='utf-8'), file=f)
            print("</div>", file=f)
        if metrics_ok:
            print("\n## Metrics\n", file=f)
            print("See metrics (not indexed by search): [metrics](metrics/)", file=f)
        if report_ok:
            print("\n## QC Report\n", file=f)
            print("See the full report (not indexed by search): [report](report/)", file=f)
        elif not EXTRACT_WITH_RDFLIB_ONLY:
            print("\n!!! warning \"QC report\"\n    ROBOT report could not be generated.\n", file=f)
    return page_rel

def build_patterns_index(pattern_pages):
    from collections import defaultdict
    tree: dict[str, dict[str, list[Path]]] = defaultdict(lambda: defaultdict(list))
    for md, ont, req in pattern_pages:
        tree[ont][req].append(md)

    with open_virtual(Path("patterns/index.md"), "w") as f:
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

    with open_virtual(Path("ProcessODPs.md"), "w") as f:
        print("# Process ODPs\n", file=f)
        print("Here is the list of Ontology Design Patterns (ODPs) aligned with process modeling requirements in the Materials Science and Engineering (MSE) domain.\n", file=f)
        print("It aligns with the three core requirements identified in the paper:\n", file=f)
        print("1. **Requirement 1: Process Structure** — Model processes, sub-processes, steps, and execution order.\n", file=f) 
        print("2. **Requirement 2: Data & Resources** — Capture inputs, outputs, and parameters per step (e.g., temperature, pressure, atmosphere, instruments, calibration).\n", file=f)
        print("3. **Requirement 3: Project & Roles** — Represent project goals, stages, agents, and their roles (e.g., synthesis, microscopy, simulation).\n", file=f)
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

# ================= All Terms bundle =================
def build_all_terms_page(all_terms: list):
    total = len(all_terms)
    log(f"All Terms aggregate size before sort: {total}")
    all_terms_sorted = sorted(all_terms, key=lambda r: (r.get("LABEL","") or "").lower())

    # CSV
    csv_rel = Path("terms/all-terms.csv")
    with open_virtual(csv_rel, "w") as cf:
        writer = csv.writer(cf)
        writer.writerow(["IRI", "LABEL", "LOCAL", "TYPE", "SOURCE", "LINK", "ALT_LABELS", "SYNONYMS", "COMMENT"])
        for r in all_terms_sorted:
            writer.writerow([
                r.get("IRI",""), r.get("LABEL",""), r.get("LOCAL",""), r.get("TYPE",""),
                f"{r.get('SOURCE_KIND','')} : {r.get('SOURCE_NAME','')}", r.get("LINK",""),
                r.get("ALT_LABELS",""), r.get("SYNONYMS",""), r.get("COMMENT",""),
            ])
    log(f"All Terms CSV rows written: {len(all_terms_sorted)}")

    # JSON for finder
    json_rel = Path("terms/all-terms.json")
    with open_virtual(json_rel, "w") as jf:
        jf.write(json.dumps(all_terms_sorted, ensure_ascii=False))

    # Index (excluded from search)
    md_rel = Path("terms/index.md")
    with open_virtual(md_rel, "w") as f:
        print("---", file=f)
        print("search:", file=f)
        print("  exclude: true", file=f)
        print("---\n", file=f)
        print("# All Terms\n", file=f)
        print(f"[Download CSV]({csv_rel.name}) · [Interactive finder](find/)\n", file=f)
        if not all_terms_sorted:
            print("> _No terms were extracted. Check the build log for counts and any errors._\n", file=f)
        print("| IRI | Label | Local | Type | Source | Link | Alt labels | Synonyms | Comment |", file=f)
        print("| --- | --- | --- | --- | --- | --- | --- | --- | --- |", file=f)
        for r in all_terms_sorted:
            iri   = (r.get("IRI","") or "").replace("|","\\|")
            label = (r.get("LABEL","") or "").replace("|","\\|")
            local = (r.get("LOCAL","") or "").replace("|","\\|")
            typ   = (r.get("TYPE","") or "").replace("|","\\|")
            src   = (f"{r.get('SOURCE_KIND','')} : {r.get('SOURCE_NAME','')}" or "").replace("|","\\|")
            link  = r.get("LINK","")
            alt   = (r.get("ALT_LABELS","") or "").replace("|","\\|")
            syn   = (r.get("SYNONYMS","") or "").replace("|","\\|")
            com   = (r.get("COMMENT","") or "").replace("|","\\|")
            # Render a data attribute; we'll rewrite it via JS to prefix the site base.
            print(f'| <{iri}> | {label} | `{local}` | {typ} | {src} | <a data-site-link="{link}">open</a> | {alt} | {syn} | {com} |', file=f)

        print("\n<script>", file=f)
        print(r"""(function(){
    function siteBase(){
        const parts = window.location.pathname.split('/').filter(Boolean);
        return parts.length ? ('/' + parts[0] + '/') : '/';
    }
    const base = siteBase();
    document.querySelectorAll('a[data-site-link]').forEach(a=>{
        const rel = a.getAttribute('data-site-link') || '';
        a.setAttribute('href', base + rel.replace(/^\/+/, ''));
    });
    })();""", file=f)
        print("</script>", file=f)
    # Finder UI — enhanced with filters, fuzzy matching, result highlighting, keyboard nav
    find_rel = Path(“terms/find.md”)
    with open_virtual(find_rel, “w”) as f:
        print(“# Find Terms\n”, file=f)
        print(“> Search across all ontologies and patterns. Filter by type, source, or requirement.\n”, file=f)
        print(“””<style>
#search-box{display:flex;gap:0.5rem;flex-wrap:wrap;align-items:center}
#q{flex:1;min-width:200px;padding:0.7rem 1rem;font-size:1rem;border:2px solid var(--md-default-fg-color--lighter);border-radius:8px;background:var(--md-default-bg-color);color:var(--md-default-fg-color);transition:border-color .2s}
#q:focus{outline:none;border-color:var(--md-accent-fg-color)}
#clear-btn{padding:0.7rem 1rem;border:none;border-radius:8px;background:var(--md-default-fg-color--lightest);color:var(--md-default-fg-color);cursor:pointer;font-size:0.9rem}
#clear-btn:hover{background:var(--md-accent-fg-color);color:#fff}
.filters{display:flex;gap:0.5rem;flex-wrap:wrap;margin-top:0.5rem}
.filters select{padding:0.4rem 0.6rem;border:1px solid var(--md-default-fg-color--lighter);border-radius:6px;background:var(--md-default-bg-color);color:var(--md-default-fg-color);font-size:0.85rem}
#stats{margin-top:0.5rem;font-size:0.85rem;opacity:0.7}
#results{margin-top:1rem}
.term-card{border:1px solid var(--md-default-fg-color--lightest);border-radius:8px;padding:0.8rem 1rem;margin-bottom:0.5rem;transition:box-shadow .15s}
.term-card:hover{box-shadow:0 2px 8px rgba(0,0,0,.1)}
.term-label{font-weight:600;font-size:1.05rem}
.term-type{display:inline-block;padding:0.1rem 0.5rem;border-radius:4px;font-size:0.75rem;font-weight:500;margin-left:0.5rem;background:var(--md-accent-fg-color--transparent);color:var(--md-accent-fg-color)}
.term-meta{font-size:0.85rem;color:var(--md-default-fg-color--light);margin-top:0.3rem}
.term-meta a{color:var(--md-accent-fg-color)}
.term-comment{font-size:0.85rem;margin-top:0.3rem;font-style:italic;opacity:0.8}
mark{background:var(--md-accent-fg-color--transparent);color:inherit;padding:0 2px;border-radius:2px}
.source-group{margin-top:1.5rem}
.source-group h3{margin-bottom:0.5rem;border-bottom:2px solid var(--md-accent-fg-color);padding-bottom:0.3rem;display:inline-block}
.no-results{text-align:center;padding:2rem;opacity:0.6;font-size:1.1rem}
.view-toggle{display:flex;gap:0.3rem;margin-top:0.5rem}
.view-toggle button{padding:0.3rem 0.7rem;border:1px solid var(--md-default-fg-color--lighter);border-radius:4px;background:none;color:var(--md-default-fg-color);cursor:pointer;font-size:0.8rem}
.view-toggle button.active{background:var(--md-accent-fg-color);color:#fff;border-color:var(--md-accent-fg-color)}
</style>

<div id=”search-box”>
  <input id=”q” placeholder=”Search terms… (e.g., process, temperature, agent)” autocomplete=”off”>
  <button id=”clear-btn” title=”Clear search”>Clear</button>
</div>
<div class=”filters”>
  <select id=”f-type”><option value=””>All types</option></select>
  <select id=”f-source”><option value=””>All sources</option></select>
  <select id=”f-kind”><option value=””>Ontologies & Patterns</option><option value=”Ontology”>Ontologies only</option><option value=”Pattern”>Patterns only</option></select>
</div>
<div class=”view-toggle”>
  <button id=”view-grouped” class=”active” title=”Group by source”>Grouped</button>
  <button id=”view-flat” title=”Show all results”>Flat list</button>
</div>
<div id=”stats”></div>
<div id=”results”></div>
“””, file=f)
        print(“<script>”, file=f)
        print(r”””(function(){
const $ = sel => document.querySelector(sel);
const results = $('#results');
const stats = $('#stats');
const input = $('#q');
const clearBtn = $('#clear-btn');
const fType = $('#f-type');
const fSource = $('#f-source');
const fKind = $('#f-kind');
const viewGrouped = $('#view-grouped');
const viewFlat = $('#view-flat');
let viewMode = 'grouped';

function siteBase(){
  const parts = window.location.pathname.split('/').filter(Boolean);
  return parts.length ? ('/' + parts[0] + '/') : '/';
}

/* Fuzzy match: splits query into tokens; all tokens must appear somewhere */
function fuzzyMatch(r, tokens){
  const hay = [r.LABEL, r.LOCAL, r.IRI, r.ALT_LABELS, r.SYNONYMS, r.COMMENT]
    .map(x => (x||'').toLowerCase()).join(' ');
  return tokens.every(t => hay.includes(t));
}

function highlight(text, tokens){
  if(!text || !tokens.length) return text || '';
  let s = text.replace(/</g,'&lt;').replace(/>/g,'&gt;');
  for(const t of tokens){
    const re = new RegExp('(' + t.replace(/[.*+?^${}()|[\]\\]/g,'\\$&') + ')','gi');
    s = s.replace(re, '<mark>$1</mark>');
  }
  return s;
}

function renderCard(r, tokens, base){
  const label = highlight(r.LABEL || r.LOCAL || '', tokens);
  const local = r.LOCAL ? highlight(r.LOCAL, tokens) : '';
  const typ = r.TYPE || 'Entity';
  const link = base + (r.LINK || '').replace(/^\/+/, '');
  const source = `${r.SOURCE_KIND || ''}: ${r.SOURCE_NAME || ''}`;
  const comment = r.COMMENT ? highlight(r.COMMENT.substring(0, 200), tokens) : '';
  const alt = r.ALT_LABELS ? highlight(r.ALT_LABELS, tokens) : '';
  return `<div class=”term-card”>
    <div><span class=”term-label”>${label}</span><span class=”term-type”>${typ}</span></div>
    <div class=”term-meta”><code>${local}</code> &mdash; <a href=”${link}”>${source}</a></div>
    ${comment ? `<div class=”term-comment”>${comment}</div>` : ''}
    ${alt ? `<div class=”term-meta”>Also: ${alt}</div>` : ''}
  </div>`;
}

function renderGrouped(subset, tokens){
  const base = siteBase();
  const groups = {};
  for(const r of subset){
    const key = `${r.SOURCE_KIND}: ${r.SOURCE_NAME}`;
    if(!groups[key]) groups[key] = {link: r.LINK, items: []};
    groups[key].items.push(r);
  }
  let html = '';
  for(const key of Object.keys(groups).sort()){
    const g = groups[key];
    html += `<div class=”source-group”><h3>${key} (${g.items.length})</h3>`;
    const shown = g.items.slice(0, 20);
    for(const r of shown) html += renderCard(r, tokens, base);
    if(g.items.length > 20) html += `<p style=”opacity:0.6”>… and ${g.items.length - 20} more</p>`;
    html += '</div>';
  }
  return html;
}

function renderFlat(subset, tokens){
  const base = siteBase();
  const MAX = 100;
  let html = '';
  const shown = subset.slice(0, MAX);
  for(const r of shown) html += renderCard(r, tokens, base);
  if(subset.length > MAX) html += `<p style=”opacity:0.6”>Showing ${MAX} of ${subset.length} results.</p>`;
  return html;
}

let DATA = [];
let allTypes = new Set();
let allSources = new Set();

fetch('../all-terms.json')
.then(r=>{ if(!r.ok) throw new Error('Failed to load all-terms.json: ' + r.status); return r.json(); })
.then(rows=>{
  DATA = rows;
  for(const r of rows){
    if(r.TYPE) allTypes.add(r.TYPE);
    if(r.SOURCE_NAME) allSources.add(r.SOURCE_NAME);
  }
  for(const t of [...allTypes].sort()) fType.innerHTML += `<option value=”${t}”>${t}</option>`;
  for(const s of [...allSources].sort()) fSource.innerHTML += `<option value=”${s}”>${s}</option>`;
  stats.textContent = `${rows.length} terms loaded. Start typing to search.`;
})
.catch(err=>{
  stats.textContent = 'Error: ' + err.message;
});

function doSearch(){
  const raw = input.value.trim();
  const tokens = raw.toLowerCase().split(/\s+/).filter(Boolean);
  const typeF = fType.value;
  const sourceF = fSource.value;
  const kindF = fKind.value;

  if(!tokens.length && !typeF && !sourceF && !kindF){
    results.innerHTML = '';
    stats.textContent = `${DATA.length} terms loaded. Start typing to search.`;
    return;
  }

  let subset = DATA;
  if(tokens.length) subset = subset.filter(r => fuzzyMatch(r, tokens));
  if(typeF) subset = subset.filter(r => r.TYPE === typeF);
  if(sourceF) subset = subset.filter(r => r.SOURCE_NAME === sourceF);
  if(kindF) subset = subset.filter(r => r.SOURCE_KIND === kindF);

  const ontoCount = new Set(subset.filter(r=>r.SOURCE_KIND==='Ontology').map(r=>r.SOURCE_NAME)).size;
  const patCount = new Set(subset.filter(r=>r.SOURCE_KIND==='Pattern').map(r=>r.SOURCE_NAME)).size;
  stats.textContent = `${subset.length} terms found across ${ontoCount} ontologies and ${patCount} patterns.`;

  if(!subset.length){
    results.innerHTML = '<div class=”no-results”>No matching terms found. Try a different query or adjust filters.</div>';
    return;
  }

  results.innerHTML = viewMode === 'grouped' ? renderGrouped(subset, tokens) : renderFlat(subset, tokens);
}

let debounce;
input.addEventListener('input', ()=>{ clearTimeout(debounce); debounce = setTimeout(doSearch, 150); });
fType.addEventListener('change', doSearch);
fSource.addEventListener('change', doSearch);
fKind.addEventListener('change', doSearch);
clearBtn.addEventListener('click', ()=>{ input.value=''; fType.value=''; fSource.value=''; fKind.value=''; doSearch(); input.focus(); });

viewGrouped.addEventListener('click', ()=>{ viewMode='grouped'; viewGrouped.classList.add('active'); viewFlat.classList.remove('active'); doSearch(); });
viewFlat.addEventListener('click', ()=>{ viewMode='flat'; viewFlat.classList.add('active'); viewGrouped.classList.remove('active'); doSearch(); });

/* Keyboard shortcut: press / to focus search */
document.addEventListener('keydown', (e)=>{
  if(e.key === '/' && document.activeElement !== input){ e.preventDefault(); input.focus(); }
  if(e.key === 'Escape' && document.activeElement === input){ input.blur(); }
});
})();”””, file=f)
        print(“</script>”, file=f)


# ================= Main =================
def main():
    all_terms = []

    onto_files = discover_ontologies()
    onto_pages = []
    for p, relroot in onto_files:
        try:
            onto_pages.append((make_ontology_page(p, relroot, all_terms), relroot))
        except Exception as e:
            log(f"[ERROR] ontology page failed for {p.name}: {e}")
    build_ontology_index(onto_pages)

    pat_files = discover_patterns()
    pat_pages = []
    for p, ont, req in pat_files:
        try:
            pat_pages.append((make_pattern_page(p, ont, req, all_terms), ont, req))
        except Exception as e:
            log(f"[ERROR] pattern page failed for {p.name}: {e}")
    build_patterns_index(pat_pages)

    build_all_terms_page(all_terms)

if __name__ == "__main__":
    main()
