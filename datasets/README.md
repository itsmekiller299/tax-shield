# FinReady datasets

FinReady is a deterministic tax-readiness platform for FY 2025–26 / AY 2026–27. This repository supports income and transaction organisation, tax and filing readiness, evidence tracking, AIS/Form 26AS reconciliation, deterministic risks, readiness scoring, and scenarios.

`01_tax_rules` through `05_evidence` contain scoped official-source-backed reference data. Every official record retains its source URL. `06_intelligence` contains transparent project-defined deterministic configuration, not tax law. `07_synthetic_demo` contains realistic test/demo records marked `data_type=synthetic` and `synthetic_source=generated_for_testing`; it contains no real taxpayer information.

No AI, ML, LLM, RAG, embeddings, or paid AI services are used. This is not professional tax advice. The repository intentionally excludes broad legal dumps and any rule area for which project-relevant complete, verified source coverage has not been established.
