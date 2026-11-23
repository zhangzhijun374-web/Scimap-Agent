# Visualization guide

## Default publication style

SciMap-Agent uses the `journal-cluster` style by default. Users do not need to manually tune ordinary visual parameters. The renderer automatically applies:

- A compact ForceAtlas2 network layout (NetworkX spring-layout fallback when ForceAtlas2 is unavailable).
- A restrained red / blue / green / ochre / purple cluster palette.
- Curved, translucent co-occurrence links; within-cluster links inherit the cluster color and cross-cluster links are visually quieter.
- Node size proportional to document frequency.
- Soft elliptical cluster boundaries with dashed outlines and a very light cluster tint.
- Automatically generated cluster headings based on the two most frequent non-overlapping terms in each detected cluster.
- Importance-ranked keyword labels with display-space collision relaxation. Small networks label every node; larger networks select a readable subset automatically.
- PNG, SVG, and PDF output. SVG/PDF retain editable text where supported by the selected font.

The overlay map uses average publication year for node color while retaining the same layout and cluster boundary system. The density map uses a smoothed density surface over the same network coordinates.

## Reproducibility and interpretation

Record the occurrence threshold, counting method, normalization method, community algorithm, layout algorithm, seed, and figure resolution. Cluster headings are concise, data-derived descriptors, not validated semantic labels. Review them before publication. Keep the underlying network data unchanged when adjusting display settings. A network layout is not geographic space.

VOSviewer-compatible exports are generated as map/network text files and JSON. Open them in VOSviewer or VOSviewer Online for interactive inspection and, if desired, use VOSviewer's own layout and visualization controls.

## v0.4.3 defaults

Figures use 600-dpi PNG, SVG and PDF. For typography, English/numerals prefer Times New Roman when installed, else a serif fallback. For recognized grouped XLSX, the A/B average-publication-year overlay uses a 2016–2026 legend at two-year ticks, with curved edges colored as a gradient between endpoint-node colors. All paths and titles are presentation aids, not additional scientific estimates.
