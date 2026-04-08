---
hide:
  - toc
---

<div class="odp-hero">
  <h1>Ontology Design Patterns for MSE</h1>
  <p>Reusable solutions for modeling processes, data, and projects in Materials Science & Engineering. Explore patterns, search terms, and shape what comes next.</p>
  <div class="odp-hero-actions">
    <a href="ProcessODPs/" class="odp-btn odp-btn-white">Browse Patterns</a>
    <a href="terms/find/" class="odp-btn odp-btn-outline">Search Terms</a>
    <a href="community/" class="odp-btn odp-btn-outline">Vote & Contribute</a>
  </div>
</div>

<div class="odp-stats">
  <div class="odp-stat">
    <span class="odp-stat-num">12</span>
    <span class="odp-stat-label">Ontologies</span>
  </div>
  <div class="odp-stat">
    <span class="odp-stat-num">8</span>
    <span class="odp-stat-label">ODPs</span>
  </div>
  <div class="odp-stat">
    <span class="odp-stat-num">3</span>
    <span class="odp-stat-label">Requirements</span>
  </div>
  <div class="odp-stat">
    <span class="odp-stat-num">5</span>
    <span class="odp-stat-label">Planned Domains</span>
  </div>
</div>

<h2 class="odp-section-title">Explore</h2>

<div class="odp-cards">

<a href="ProcessODPs/" class="odp-card">
  <span class="odp-card-icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M15 3a3 3 0 0 1 3 3c0 .7-.24 1.35-.65 1.85l2.65 4.6c.28-.06.56-.1.85-.1a3.07 3.07 0 0 1 .15 6.14 3 3 0 0 1-3.15-2.84h-.01l-4.06.93A3 3 0 0 1 8 20a3 3 0 0 1-2.78-4.12l-2.57-2.08A3 3 0 0 1 0 12a3 3 0 0 1 6 0c0 .7-.24 1.35-.65 1.85l2.57 2.08c.42-.3.9-.5 1.43-.58l.65-4.35A3 3 0 0 1 12 6c0 .7.24 1.35.65 1.85L15 3z"/></svg></span>
  <h3>Process ODPs</h3>
  <p>Browse extracted patterns organized by ontology and requirement — process structure, data flows, and project roles.</p>
</a>

<a href="ontologies/" class="odp-card">
  <span class="odp-card-icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M3 3h6v4H3V3m8 0h6v4h-6V3M3 9h6v4H3V9m8 0h6v4h-6V9M3 15h6v4H3v-4m8 0h6v4h-6v-4"/></svg></span>
  <h3>Ontologies</h3>
  <p>Explore source ontologies with interactive visualizations, quality reports, and downloadable files.</p>
</a>

<a href="terms/find/" class="odp-card">
  <span class="odp-card-icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M9.5 3A6.5 6.5 0 0 1 16 9.5c0 1.61-.59 3.09-1.56 4.23l.27.27h.79l5 5-1.5 1.5-5-5v-.79l-.27-.27A6.52 6.52 0 0 1 9.5 16 6.5 6.5 0 0 1 3 9.5 6.5 6.5 0 0 1 9.5 3m0 2C7 5 5 7 5 9.5S7 14 9.5 14 14 12 14 9.5 12 5 9.5 5z"/></svg></span>
  <h3>Find Terms</h3>
  <p>Search across all terms with filters by type, source ontology, and fuzzy matching.</p>
</a>

<a href="community/" class="odp-card">
  <span class="odp-card-icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M18 13h-2.09a5.98 5.98 0 0 1-3.91 3.91V19h2v2H10v-2h2v-2.09A5.98 5.98 0 0 1 6 11V4h2V2h2v2h4V2h2v2h2v7a5.98 5.98 0 0 1-4 5.66V19h2v2h-2v-2h-2v-2.09A6.01 6.01 0 0 1 18 11V4h-2V2h2v2h2v7h-2z"/></svg></span>
  <h3>Community Hub</h3>
  <p>Vote for domains, propose new patterns, and help shape the future of this catalog.</p>
</a>

</div>

---

<h2 class="odp-section-title">Three Core Requirements</h2>

This project addresses three fundamental modeling needs in MSE, identified in our [featured paper](https://arxiv.org/abs/2509.23776):

<div class="odp-cards">

<div class="odp-card">
  <span class="odp-card-icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M6.99 11L3 15l3.99 4v-3H14v-2H6.99v-3zM21 9l-3.99-4v3H10v2h7.01v3L21 9z"/></svg></span>
  <h3>Req 1: Process Structure</h3>
  <p>Model processes, sub-processes, steps, and execution order.</p>
</div>

<div class="odp-card">
  <span class="odp-card-icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M6 22a3 3 0 0 1-3-3c0-1.29.82-2.39 1.96-2.81L3 12h2l1.91 3.97C7.58 16.15 8 16.54 8 17h8c0-.46.42-.85 1.09-1.03L19 12h2l-1.96 4.19A3 3 0 0 1 21 19a3 3 0 0 1-3 3H6m1-8l1-8h8l1 8H7m5-10a2 2 0 0 1-2-2 2 2 0 0 1 2-2 2 2 0 0 1 2 2 2 2 0 0 1-2 2z"/></svg></span>
  <h3>Req 2: Data & Resources</h3>
  <p>Capture inputs, outputs, and parameters — temperature, pressure, instruments, calibration.</p>
</div>

<div class="odp-card">
  <span class="odp-card-icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M16 17v2H2v-2s0-4 7-4 7 4 7 4m-3.5-9.5A3.5 3.5 0 1 0 9 11a3.5 3.5 0 0 0 3.5-3.5m3.44 5.5A5.32 5.32 0 0 1 18 17v2h4v-2s0-3.63-6.06-4M15 4a3.39 3.39 0 0 0-1.93.59 5 5 0 0 1 0 5.82A3.39 3.39 0 0 0 15 11a3.5 3.5 0 0 0 0-7z"/></svg></span>
  <h3>Req 3: Project & Roles</h3>
  <p>Represent goals, stages, agents, and roles — synthesis, microscopy, simulation.</p>
</div>

</div>

!!! info "More patterns coming"
    We are actively developing patterns for material composition, measurement, simulation, provenance, and standards compliance. **[Vote for what matters to you](community/)** or see the [Roadmap](roadmap/).

---

<h2 class="odp-section-title">Cite this Work</h2>

> **Semantic Representation of Processes with Ontology Design Patterns**
> *Ebrahim Norouzi, Sven Hertling, Jorg Waitelonis, and Harald Sack*
> arXiv:2509.23776 — [https://arxiv.org/abs/2509.23776](https://arxiv.org/abs/2509.23776)

See the [Citation page](cite/) for BibTeX, APA, RIS, and copy-to-clipboard options.
