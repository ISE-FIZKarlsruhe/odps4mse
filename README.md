# Ontology Design Patterns for Materials Science and Engineering

This repository provides a baseline framework for extracting Ontology Design Patterns (ODPs) in the Materials Science and Engineering (MSE) domain.

## Repository Structure

- **GroundtruthTerms/** – Contains manually curated ground truth terms for evaluation.
- **ODPs/** – ODPs useful for the MSE domain.
- **Ontologies/** – Source ontologies used for pattern extraction and evaluation.
- **Patterns/** – Extracted and manually curated ontology design patterns per requirement.
- **ODP_Extractor_baseline.ipynb** – Jupyter notebook implementing the baseline method for semantic similarity-based pattern extraction.
- **Latex.ipynb** – Notebook to support LaTeX output generation for documentation.
- **run.bat** – Batch script for executing the ROBOT tool for the ontology modules construction.

## Method Summary

The extraction pipeline uses semantic similarity matching between textual requirements and ontology elements (IRIs), transforming textual descriptions into embedding-based queries. The approach supports identifying reusable patterns across different ontologies such as PMDcore, P-PLAN, M4I, and GPO.

## How to Use

1. Prepare requirements and prepare the Ground Truth dataset in [`Miro Board`](https://miro.com/app/board/uXjVNsagu1I=/?share_link_id=85458131985).
2. Run [ODP Extractor baseline](ODP_Extractor_baseline.ipynb) to extract matching ontology elements.
3. Review and organize resulting IRIs into candidate ODPs in `ODPs/`.

## Evaluation

The evaluation framework assesses precision, recall, and F1-score per pattern category:
- **Process ODP** (Requirement 1)
- **Resource ODP** (Requirement 2)
- **Project ODP** (Requirement 3)

Performance varies depending on annotation richness and alignment of the ontology with MSE-specific semantics.

## License

[MIT License](License.txt)
