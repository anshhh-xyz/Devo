# Devo

Devo is an **evidence-first coding assistant** for local Python projects. It makes one approved code change, runs a fixed check before and after, and reports what the check actually showed.

It computes verdicts purely from real test execution results — model prose never influences verdicts.

## Status

Devo is currently under active development for the Devpost **Build with AI: Basics** hackathon.

## Planned Journey

1. **Inspect:** Target workspace inspection with boundary containment.
2. **Baseline:** Run fixed check (`pytest`) on original files.
3. **Plan & Diff:** Model proposes structured edits; Devo generates a unified diff.
4. **Approve:** Human user explicitly approves the exact diff hash.
5. **Apply & Verify:** Apply change, rerun check, and compute honest verdict (`Verified`, `Verification failed`, or `Not verified`).
6. **Revert:** Safe, hash-checked rollback at any time.

## License

[MIT](LICENSE)
