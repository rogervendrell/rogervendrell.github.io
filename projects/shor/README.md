# Shor's Factorization Algorithm — Project Site

A static project page for our from-scratch Qiskit implementation of Shor's factorization
algorithm (KTH, DD2367). Adapted from the group's LaTeX report (`../latex/`) into a single
`index.html`, using the same figures the report uses.

## Structure

- `index.html` — the whole page (hero, abstract, problem statement, method walkthrough with
  every gate we built, results, discussion, references).
- `static/images/project/` — figures copied from the report (`../latex/images/project/`).
- `static/images/teaser-circuit.svg` — the hand-drawn hero diagram.
- `static/pdf/shors-algorithm-report.pdf` — the rendered report, linked from the "Report" button.
- `static/css/index.css`, `static/js/index.js` — page-specific styling and the navbar toggle.

Math is rendered client-side with MathJax (configured with `\ket`/`\bra`/`\braket` macros to
match the report's `braket` package notation), loaded from CDN — an internet connection is
needed to view the page correctly.

## Before publishing

- The "Code" button and footer GitHub icon point at
  `github.com/rogervendrell/shors-algorithm-from-scratch` — make sure that repo actually exists
  at that URL before the link goes live (see `../repository/`).
- The navbar home icon (`href="#"`) should point at the parent portfolio site once this page is
  deployed under it.

## Local preview

```bash
cd static-site
python3 -m http.server 8000
# open http://localhost:8000
```

## Origin

This template is adapted from the [Nerfies project page](https://nerfies.github.io), licensed
under a [Creative Commons Attribution-ShareAlike 4.0 International License](http://creativecommons.org/licenses/by-sa/4.0/).
