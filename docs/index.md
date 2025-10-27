# Ontology Design Patterns

Dive into a comprehensive repository of **Ontology Design Patterns (ODPs)** — reusable solutions to common ontology modeling challenges.  
Explore, contribute, and collaborate with a global community of ontology practitioners. Together, we create smarter, more connected data ecosystems.

> **Featured paper**  
> **Semantic Representation of Processes with Ontology Design Patterns**  
> *Ebrahim Norouzi, Sven Hertling, Jörg Waitelonis, and Harald Sack*  
> arXiv:2509.23776 — <https://arxiv.org/abs/2509.23776>

---

## What’s in scope?

This repository focuses on ODPs for **process modeling** in Materials Science & Engineering (MSE).  
It aligns with the three core requirements identified in the paper:

1. **Process Structure** — Model processes, sub-processes, steps, and execution order.  
2. **Data & Resources** — Capture inputs, outputs, and parameters per step (e.g., temperature, pressure, atmosphere, instruments, calibration).  
3. **Project & Roles** — Represent project goals, stages, agents, and their roles (e.g., synthesis, microscopy, simulation).

You’ll find extracted patterns and reusable modules derived from ontologies such as **P-PLAN**, **PMDcore**, **M4I**, **OPMW**, and **GPO**.

---

## How to start

1. Create a new [`issue`](https://github.com/ISE-FIZKarlsruhe/odps4mse/issues) describing your pattern idea or contribution.  
2. Copy the template from [`patterns/template.md`](https://github.com/ISE-FIZKarlsruhe/odps4mse/patterns/template.md) into a new folder for your pattern.  
3. Fill the template with all key information (motivation, intent, competency questions, diagram, examples, references).  
4. Add a link to your new pattern in the appropriate index page or collection.

> Tip: If your pattern targets one of the three requirements above, mention it explicitly so others can discover it quickly.

---

## Cite this work

If this repository or its methodology helps your research, please cite:

```bibtex
@article{norouzi2025semantic,
  title={Semantic Representation of Processes with Ontology Design Patterns},
  author={Norouzi, Ebrahim and Hertling, Sven and Waitelonis, J{\"o}rg and Sack, Harald},
  journal={arXiv preprint arXiv:2509.23776},
  year={2025},
  url={https://arxiv.org/abs/2509.23776}
}
