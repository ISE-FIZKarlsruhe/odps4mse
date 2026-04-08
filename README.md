# Ontology Design Patterns for Materials Science and Engineering

[![Build & Deploy](https://github.com/ISE-FIZKarlsruhe/odps4mse/actions/workflows/deploy.yml/badge.svg)](https://github.com/ISE-FIZKarlsruhe/odps4mse/actions/workflows/deploy.yml)
[![Validate](https://github.com/ISE-FIZKarlsruhe/odps4mse/actions/workflows/validate.yml/badge.svg)](https://github.com/ISE-FIZKarlsruhe/odps4mse/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Documentation](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://ise-fizkarlsruhe.github.io/odps4mse/)

This repository provides a baseline framework for extracting **Ontology Design Patterns (ODPs)** in the **Materials Science and Engineering (MSE)** domain.  
It accompanies the paper:

> **Semantic Representation of Processes with Ontology Design Patterns**  
> *Ebrahim Norouzi, Sven Hertling, Jörg Waitelonis, and Harald Sack*  
> arXiv:2509.23776 — [https://arxiv.org/abs/2509.23776](https://arxiv.org/abs/2509.23776)

---

## Documentation

Browse the full documentation and interactive tools at **[ise-fizkarlsruhe.github.io/odps4mse](https://ise-fizkarlsruhe.github.io/odps4mse/)**.

Features include:
- Interactive **pattern visualization** via [ontoink](https://pypi.org/project/ontoink/)
- **Term search** with filters across all ontologies and patterns
- Automatically generated **quality reports** and **metrics** per ontology
- **Download** links for all source files

---

## Repository Structure

- **Ontologies/** — Source ontologies used for pattern extraction and evaluation.
- **Patterns/** — Extracted and manually curated ontology design patterns per requirement.
- **ODPs/** — Reusable ODPs for the MSE domain.
- **GroundtruthTerms/** — Manually curated ground truth terms for evaluation.
- **ODP_Extractor_baseline.ipynb** — Jupyter notebook implementing the baseline method for semantic similarity-based pattern extraction.
- **docs/** — MkDocs documentation source (auto-deployed to GitHub Pages).

---

## Method Summary

The extraction pipeline uses semantic similarity matching between textual requirements and ontology elements (IRIs), transforming textual descriptions into embedding-based queries. The approach supports identifying reusable patterns across different ontologies such as PMDcore, P-PLAN, M4I, and GPO.

---

## How to Use

1. Prepare requirements and the Ground Truth dataset in [`Miro Board`](https://miro.com/app/board/uXjVNsagu1I=/?share_link_id=85458131985).
2. Run [ODP Extractor baseline](ODP_Extractor_baseline.ipynb) to extract matching ontology elements.
3. Review and organize resulting IRIs into candidate ODPs in `ODPs/`.

---

## Evaluation

The evaluation framework assesses precision, recall, and F1-score per pattern category:

- **Process ODP** (Requirement 1)
- **Resource ODP** (Requirement 2)
- **Project ODP** (Requirement 3)

Performance varies depending on annotation richness and alignment of the ontology with MSE-specific semantics.

---

## Contributing

We welcome contributions of new patterns, ontologies, and improvements. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## Citation

If you use this repository or methodology in your research, please cite:

```bibtex
@article{norouzi2025semantic,
  title={Semantic Representation of Processes with Ontology Design Patterns},
  author={Norouzi, Ebrahim and Hertling, Sven and Waitelonis, J{\"o}rg and Sack, Harald},
  journal={arXiv preprint arXiv:2509.23776},
  year={2025},
  url={https://arxiv.org/abs/2509.23776}
}
```

See also the [citation page](https://ise-fizkarlsruhe.github.io/odps4mse/cite/) for APA and RIS formats, or use GitHub's built-in **"Cite this repository"** button (powered by [`CITATION.cff`](CITATION.cff)).

---

## License

[MIT License](LICENSE)
