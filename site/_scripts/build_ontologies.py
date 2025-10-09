import os, subprocess, pathlib, html
from pathlib import Path
import mkdocs_gen_files

ROOT = Path(__file__).resolve().parents[2]
ONTO_DIR = ROOT / "Ontologies"
OUT_DIR  = ROOT / "docs" / "ontologies"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def run(cmd):
    subprocess.run(cmd, check=True)

def robot_report(infile: Path, outdir: Path):
    outdir.mkdir(parents=True, exist_ok=True)
    tsv = outdir / "report.tsv"
    run(["robot", "report", "-i", str(infile), "--output", str(tsv)])
    # Convert to a tiny Markdown table for indexing
    # (keep it small; link to full TSV for details)
    rows = []
    with open(tsv, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i > 100: break  # cap to keep page lean
            rows.append(line.rstrip("\n").split("\t"))
    # pipe through Pandas-like rendering only if you want prettier tables;
    # for simplicity, write basic Markdown:
    md = []
    if rows:
        header = rows[0]
        md.append("| " + " | ".join(header) + " |")
        md.append("| " + " | ".join(["---"]*len(header)) + " |")
        for r in rows[1:]:
            md.append("| " + " | ".join(r) + " |")
    (outdir / "report.md").write_text("\n".join(md) or "_No issues found._", encoding="utf-8")
    return tsv

def robot_export_entities(infile: Path, outdir: Path):
    # Single HTML table containing ID/LABEL/TYPE so search can find terms.
    html_out = outdir / "entities.html"
    run([
        "robot","export","-i",str(infile),
        "--header","ID|LABEL|TYPE",
        "--export",str(html_out)
    ])
    return html_out

def make_page(infile: Path):
    name = infile.stem
    odir = OUT_DIR / name
    odir.mkdir(parents=True, exist_ok=True)

    # Run ROBOT tasks
    try:
        tsv = robot_report(infile, odir)
        entities_html = robot_export_entities(infile, odir)
    except Exception as e:
        # Create a fallback page if ROBOT fails
        entities_html = None

    # Write Markdown page
    md_path = Path(f"ontologies/{name}.md")
    with mkdocs_gen_files.open(md_path, "w") as f:
        print(f"# {name}", file=f)
        print("", file=f)
        print(f"- **Source:** `{infile.relative_to(ROOT)}`", file=f)
        if (odir / "report.tsv").exists():
            print(f"- **ROBOT report (TSV):** [{name} report](./{name}/report.tsv)", file=f)
        print("", file=f)

        # Embed entities table (search will index these terms)
        if entities_html and entities_html.exists():
            html_str = entities_html.read_text(encoding="utf-8")
            print("## Classes & Properties", file=f)
            print("", file=f)
            print("<div class='entities-table'>", file=f)
            print(html_str, file=f)
            print("</div>", file=f)

        # Short report preview for human readers + indexing
        if (odir / "report.md").exists():
            print("\n## QC Report (preview)\n", file=f)
            print((odir / "report.md").read_text(encoding="utf-8"), file=f)

    return md_path

def main():
    files = []
    if ONTO_DIR.exists():
        for ext in (".owl", ".ttl", ".rdf", ".obo"):
            files += sorted(ONTO_DIR.rglob(f"*{ext}"))
    pages = [make_page(p) for p in files]

    # Build index page
    index_md = Path("ontologies/index.md")
    with mkdocs_gen_files.open(index_md, "w") as f:
        print("# Ontologies", file=f)
        print("", file=f)
        if not pages:
            print("_No ontologies found in `Ontologies/`._", file=f)
        else:
            for p in pages:
                title = p.stem
                print(f"- [{title}]({p.name})", file=f)

if __name__ == "__main__":
    main()
