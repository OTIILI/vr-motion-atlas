# VR Motion Atlas

Interactive 3D exploration of physical and virtual hand trajectories, head orientation, amplification, and target events. Developed with Olli Tiilikainen for exploratory analysis of bimanual VR interaction.

## Run locally (Windows)

Install Python 3 if needed. From this repository folder, open a terminal and run:

```powershell
py -m http.server 8000 --directory dist
```

Open http://localhost:8000. Do not open index.html directly: browsers require an HTTP server for modules and JSON loading. The viewer vendors Three.js, so npm installation is not required to view it.

Four author reference runs load automatically. Choose **Load compatible run JSON** to open additional Motion Atlas runs or comparison bundles. No study participant recordings are bundled. Imported files are read locally in your browser; the static viewer has no upload service. 

## Reference example

`examples/author-reference-results/` contains plots and numerical summaries from the author's own R1 test recording, not a study participant. Four playable conversions of these recordings are included in `dist/data/`. Regenerate them with `python tools/convert_reference.py path/to/R1.zip`. The raw archive is not bundled. Target IDs are aligned to the first reference run, not claimed identical to the study canonical IDs. Attachment transitions and goal-counter increments are shown; individual goal outcomes have not been attributed for this example. No participant questionnaire ratings or trained study forecasts are included.

## Viewer controls

Select recordings for A/B comparison; orbit, pan, zoom or use fixed views. **1st person** follows each run's head position and full orientation with an adjustable forward offset. Its 85 degree vertical field of view is schematic, not calibrated headset optics. Uncheck **Full-window trails** to reveal paths progressively. Time-series charts seek the playhead. Legends distinguish physical/virtual and recorded left/right channels. Head direction is not eye gaze.

## Data format

See `docs/data-format.md`. Use the existing private atlas's Download selected data action to export a compatible run. Only export your author reference recording for public release. Hand coordinates, targets and head basis vectors must use the same coordinate convention.

## Analysis code

`dist/spatial.js` and `dist/timeseries.js` implement reusable display metrics. `tools/` contains the research export, orientation audit and target prediction scripts. The Python scripts expect an existing analysis workspace, not arbitrary NDJSON directly. Set ATLAS_ANALYSIS_ROOT to its root. They are provided as research pipeline source and require the upstream event tables/cache described in `docs/analysis.md`. No private tables or trained study results are included. Python dependencies: `pip install -r requirements.txt`.

`bridge/` provides a Unity importer/VRChat starting point, not a tested VRChat world.

## Validation

With Node installed, run `node tools/check-public.mjs`. The four reference conversions pass schema, score, target and head-basis checks. Loading, first-person view, scrubbing and progressive trails were browser-tested in the CPU fallback. The hosted research atlas was also tested using the CPU canvas fallback; GPU and headset behaviour require local verification.

## Research limitations

This is an exploratory visualisation tool. Display sampling is not a replacement for raw-resolution coordination analysis. Event attribution and target forecasts are provisional. Forecasts rank candidates, not probabilities or confirmed intentions. Questionnaire ratings describe overall experience, not individual conditions.

## Licence

Original viewer and analysis code is licensed under the MIT License;
see LICENSE.

Author reference recordings and figures in `dist/data/` and
`examples/author-reference-results/` are licensed under CC BY 4.0;
see DATA_LICENSE.md. These materials are excluded from the MIT licence.

Third-party components retain their respective licences.
The Three.js licence is provided in `dist/vendor/THREE-LICENSE.txt`.
