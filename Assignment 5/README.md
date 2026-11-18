# MOBILE COMPUTING — ASSIGNMENT 5
**Total 50 marks | Part A: 25 | Part B: 25**

Question-wise design answers, language-independent pseudocode, Mermaid architecture/build patterns, reproducible Python simulations, input datasets, tests and CSV evidence.

## Structure
- `Part-A/Assignment5_Design_Answers.md`: complete A1–A5 answers.
- `Part-B/Assignment5_Implementation_Investigation.md`: B1–B4 implementation, tests, comparison and decision note.
- `code/common.py`: shared simulation engine and CLI.
- `data/`: B1–B4 sample inputs.
- `diagrams/`: architecture and state-machine diagrams.
- `tests/`: deterministic regression tests.
- `outputs/`: generated CSV evidence and explanation.
- `requirements.txt`: standard library only.

## Run (from repository root)
```bash
python "Assignment 5/code/common.py" all
python "Assignment 5/code/common.py" b1
python "Assignment 5/code/common.py" b2
python "Assignment 5/code/common.py" b3
python "Assignment 5/code/common.py" b4
python -m unittest discover -s "Assignment 5/tests" -v
```
Python 3.9+. No third-party package needed.

## Evidence limitation
Part B is a deterministic, instrumented **simulation**, not a physical Android app or real-device benchmark. Battery, network, frame time, energy and upload time are model estimates. Use Android Studio/WorkManager and physical-device profiler evidence before making production claims. No real health or personal data is included.

Workflow: UNDERSTAND → DESIGN → CONSTRAINT-CHECK → IMPLEMENT → MEASURE → CHALLENGE → INTERPRET.
