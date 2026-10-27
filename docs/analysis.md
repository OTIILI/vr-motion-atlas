# Research pipeline inputs

The Python scripts originate from the study analysis workspace. They are not an end-to-end raw NDJSON analyser. ATLAS_ANALYSIS_ROOT replaces the original machine-specific root.

Expected inputs include event-work/cache/*.npz, corresponding *_head_rotation.npy, event-work/results/{events,phase_timeline,goal_audit}.csv, subjective-work/subjective_ratings.csv and subjective-work/run_final_scores.csv. Inspect each script for its required columns. Export writes to dist/data. Do not run it against participant inputs inside a public repository: it exports recordings and ratings.

Target prediction uses past virtual-hand proximity/approach and head direction/change, candidate ranks and leave-one-participant-out weight selection. Event-aligned backtests do not validate failed-reach intention or continuous false-positive rates. The public package includes code only, not trained weights, participant cases or aggregate study results.
