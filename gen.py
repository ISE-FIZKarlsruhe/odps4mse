from pathlib import Path
import runpy

HERE = Path(__file__).resolve()
SCRIPT = HERE.parent / "_scripts" / "build_ontologies.py"

runpy.run_path(str(SCRIPT), run_name="__main__")
