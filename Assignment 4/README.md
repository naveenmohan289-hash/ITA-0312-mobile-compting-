# ITA03-MP Mobile Computing — Assignment 4

This folder contains **Part I (design and analysis)** and **Part II (implementation, instrumentation and testing)**. Work is divided by task number so each deliverable can be checked against the assignment brief.

## Folder map
- `Part-I-Design/`: Tasks 1–6, structured architecture analysis, comparison matrices, traces, state policies and adversarial reasoning. Part I is design-only; it intentionally contains no implementation code.
- `Part-II-Engineering/`: Tasks 1–6, Python simulation/audit prototype, reproducible test inputs, expected outputs, Android instrumentation commands, diagrams and engineering notes.
- `common.py`: shared standard-library Python runner for the Part II reproducible simulations.
- `inputs/`: scenario datasets.
- `outputs/`: generated CSV/JSON results and sample console report.
- `diagrams/`: Mermaid architecture and workflow diagrams.

## Run the Part II common program
Python 3.9+; no third-party packages required.

```bash
python common.py all
python common.py task2
python common.py task3
python common.py task4
python common.py task5
python common.py task6
```

Run commands from inside the `Assignment 4` folder. The program writes result files to `outputs/`.

## Important evidence boundary
- Python simulation outputs are **reproducible model outputs**, not measurements from a physical Android/iOS device.
- No Android emulator, physical phone, Android Studio, adb, profiler, Battery Historian, Xcode or iOS device was available to this GitHub commit workflow. Part II therefore includes exact device-side commands and evidence templates. Run those commands on your own device/emulator and replace the marked **TO-COLLECT** placeholders with genuine logs/screenshots before submission.
- Part I is intentionally an engineering design specification, matching the no-IDE/no-SDK rule.
- Runtime and OS details vary by OS release and device vendor. Record the exact device model, OS build, API level and test configuration with any measured evidence.
- Do not claim model estimates as real measured battery, CPU, memory or latency values.

## Submission checklist
1. Read each task document and retain the task/subtask numbering.
2. Run `python common.py all`; inspect each CSV and JSON in `outputs/`.
3. For Android-specific Part II evidence, execute the documented adb/logcat/profiler commands and save raw outputs under `Part-II-Engineering/device-evidence/`.
4. Add screenshots with highlighted relevant lines, not just final totals.
5. Update the device configuration and assumptions in the report before submission.
