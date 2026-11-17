# Mobile Computing Assignment — Q1 to Q7

This folder contains question-wise answers, a reproducible Python implementation, and committed output summaries.

## Files
- `Answers_Q1-Q7.md` — answers, assumptions, calculations, analysis and conclusions.
- `implement_q1_q7.py` — runnable simulations for all seven questions.
- `outputs/Results_Summary.csv` — key numerical evidence from the simulations.
- `outputs/Q5_SIR_Summary.csv` — SDMA SIR threshold evidence.
- `outputs/Q5_Pattern_Reference.csv` — sampled ULA pattern reference points.

## Run the complete implementation
From the repository root:
```bash
pip install numpy
python Assignment/implement_q1_q7.py
```
The program creates question-numbered CSV result files in `Assignment/outputs/`.

## Model notes
The models are educational simulations, not vendor-grade physical-layer simulators. Assumptions such as overhead percentages, retry window, noise level, fading distribution, SIR threshold and traffic patterns are declared in the answer document and source code. Randomized experiments use fixed seeds for repeatability.
