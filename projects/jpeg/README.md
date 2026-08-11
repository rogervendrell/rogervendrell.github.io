# JPEG Image Compression — Project Site

A static project page for a from-scratch DCT-based image and video compression pipeline (KTH,
DM1580: Video Compression Project). Adapted from the group's Jupyter notebooks and PDF report
into a single `index.html`, with all photographic figures re-cropped and every plot/diagram
regenerated from the underlying data for a cleaner look than the original notebook exports.

## Structure

- `index.html` — the whole page (hero, abstract, problem statement, two-part method walkthrough,
  results, discussion, references).
- `static/images/project/method/` — the DCT basis figures, YUV channel split, extracted frame,
  and the zigzag-scan diagram.
- `static/images/project/results/` — before/after frame comparisons and the PSNR / compression
  ratio plots for both parts of the project.
- `static/css/index.css`, `static/js/index.js` — page-specific styling (shared with the `shor`
  project page) and the navbar toggle.

Math is rendered client-side with MathJax, loaded from CDN — an internet connection is needed to
view the page correctly.

## Where the figures came from

The original notebooks (`DM1580-Group14-Part1.ipynb`, `DM1580-Group14-Part2.ipynb`) load a video
file (`xylophone.mp4`, provided by the course) that isn't checked into this repo, so the
photographic frame figures (Y/U/V channels, frame 80/85/difference, before/after reconstructions)
were re-cropped from the notebooks' embedded PNG outputs to remove matplotlib chrome (titles, axis
ticks), rather than regenerated from source pixels. Every other figure — the 1D/2D DCT basis
plots, the PSNR and compression-ratio curves, and the zigzag-scan diagram — was regenerated from
scratch from the report's underlying formulas/data with a consistent, cleaner style.

## Before publishing

- The "Code" button and footer GitHub icon are placeholders (`href="#"`) — point them at the
  actual repository once it's published.
- The navbar home icon (`href="#"`) should point at the parent portfolio site once this page is
  deployed under it.

## Local preview

```bash
cd projects/jpeg
python3 -m http.server 8000
# open http://localhost:8000
```

## Origin

This template is adapted from the [Nerfies project page](https://nerfies.github.io), licensed
under a [Creative Commons Attribution-ShareAlike 4.0 International License](http://creativecommons.org/licenses/by-sa/4.0/).
