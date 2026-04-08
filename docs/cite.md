# How to Cite

If this repository or its methodology helps your research, please cite the following paper.

---

## BibTeX

<div id="bibtex-block" style="position:relative">

```bibtex
@article{norouzi2025semantic,
  title={Semantic Representation of Processes with Ontology Design Patterns},
  author={Norouzi, Ebrahim and Hertling, Sven and Waitelonis, J{\"o}rg and Sack, Harald},
  journal={arXiv preprint arXiv:2509.23776},
  year={2025},
  url={https://arxiv.org/abs/2509.23776}
}
```

<button onclick="copyText('bibtex')" style="padding:0.4rem 0.8rem;border:1px solid var(--md-default-fg-color--lighter);border-radius:6px;background:var(--md-default-bg-color);color:var(--md-default-fg-color);cursor:pointer;font-size:0.85rem" id="btn-bibtex">Copy BibTeX</button>

</div>

---

## APA

> Norouzi, E., Hertling, S., Waitelonis, J., & Sack, H. (2025). Semantic Representation of Processes with Ontology Design Patterns. *arXiv preprint arXiv:2509.23776*. [https://arxiv.org/abs/2509.23776](https://arxiv.org/abs/2509.23776)

<button onclick="copyText('apa')" style="padding:0.4rem 0.8rem;border:1px solid var(--md-default-fg-color--lighter);border-radius:6px;background:var(--md-default-bg-color);color:var(--md-default-fg-color);cursor:pointer;font-size:0.85rem" id="btn-apa">Copy APA</button>

---

## RIS

```
TY  - JOUR
TI  - Semantic Representation of Processes with Ontology Design Patterns
AU  - Norouzi, Ebrahim
AU  - Hertling, Sven
AU  - Waitelonis, Jörg
AU  - Sack, Harald
PY  - 2025
JO  - arXiv preprint arXiv:2509.23776
UR  - https://arxiv.org/abs/2509.23776
ER  -
```

<button onclick="copyText('ris')" style="padding:0.4rem 0.8rem;border:1px solid var(--md-default-fg-color--lighter);border-radius:6px;background:var(--md-default-bg-color);color:var(--md-default-fg-color);cursor:pointer;font-size:0.85rem" id="btn-ris">Copy RIS</button>

---

## GitHub Citation

This repository includes a [`CITATION.cff`](https://github.com/ISE-FIZKarlsruhe/odps4mse/blob/main/CITATION.cff) file. GitHub automatically renders a **"Cite this repository"** button on the repository page.

<script>
const citations = {
  bibtex: `@article{norouzi2025semantic,
  title={Semantic Representation of Processes with Ontology Design Patterns},
  author={Norouzi, Ebrahim and Hertling, Sven and Waitelonis, J{\\"o}rg and Sack, Harald},
  journal={arXiv preprint arXiv:2509.23776},
  year={2025},
  url={https://arxiv.org/abs/2509.23776}
}`,
  apa: `Norouzi, E., Hertling, S., Waitelonis, J., & Sack, H. (2025). Semantic Representation of Processes with Ontology Design Patterns. arXiv preprint arXiv:2509.23776. https://arxiv.org/abs/2509.23776`,
  ris: `TY  - JOUR\nTI  - Semantic Representation of Processes with Ontology Design Patterns\nAU  - Norouzi, Ebrahim\nAU  - Hertling, Sven\nAU  - Waitelonis, Jörg\nAU  - Sack, Harald\nPY  - 2025\nJO  - arXiv preprint arXiv:2509.23776\nUR  - https://arxiv.org/abs/2509.23776\nER  -`
};
function copyText(fmt){
  navigator.clipboard.writeText(citations[fmt]).then(()=>{
    const btn = document.getElementById('btn-'+fmt);
    const orig = btn.textContent;
    btn.textContent = 'Copied!';
    setTimeout(()=>{ btn.textContent = orig; }, 2000);
  });
}
</script>
