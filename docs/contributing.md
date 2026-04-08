# Contributing

We welcome contributions to this collection of Ontology Design Patterns. Whether you have a new pattern, an improvement to an existing one, or a bug fix, your help is valued.

---

## Getting Started

1. **Fork** the repository and clone it locally.
2. Create a new branch for your contribution: `git checkout -b my-pattern`
3. Make your changes following the guidelines below.
4. Push and open a **Pull Request** against `main`.

---

## Adding a New Pattern

1. Copy the template from [`Patterns/template.md`](https://github.com/ISE-FIZKarlsruhe/odps4mse/blob/main/Patterns/template.md).
2. Create a folder under `Patterns/<OntologyName>/<requirement>/`.
3. Add your pattern file (`.ttl` preferred) and fill in the template with:
    - **Motivation** — What modeling problem does this solve?
    - **Intent** — What is the goal of the pattern?
    - **Competency Questions** — What questions can be answered using this pattern?
    - **Diagram** — A visual representation (optional but recommended).
    - **Examples** — At least one usage example with instance data.
    - **References** — Links to related ontologies, papers, or standards.
4. Ensure your `.ttl` file is valid by parsing it with `rdflib` or `ROBOT`:
    ```bash
    robot report -i your-pattern.ttl --fail-on ERROR
    ```

---

## Adding a New Ontology

1. Place the ontology file (`.ttl`, `.owl`, `.rdf`, or `.obo`) in the `Ontologies/` directory.
2. The build pipeline will automatically extract entities and generate documentation.
3. If the ontology has import dependencies, ensure they are resolvable or provide a merged version.

---

## Code Style

- **Turtle files**: Use consistent prefix declarations and indentation.
- **Python**: Follow PEP 8 conventions for any build script changes.
- **Markdown**: Use standard GitHub-flavored Markdown.

---

## CI Checks

Pull requests are automatically checked by CI workflows:

- **Build Test** — The MkDocs site builds successfully with your changes.
- **Validation** — ROBOT and rdflib verify ontology and pattern files have no errors.

Please ensure all checks pass before requesting a review.

---

## Reporting Issues

Found a bug, broken link, or incorrect pattern? Open an [issue](https://github.com/ISE-FIZKarlsruhe/odps4mse/issues) with:

- A clear description of the problem.
- Steps to reproduce (if applicable).
- The affected file(s) or URL(s).
