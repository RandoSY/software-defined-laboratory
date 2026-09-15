# Cloud GSA Prototype — SDL lineage

**Source repository:** https://github.com/RandoSY/cloud-gsa-prototype

**Source snapshot:** `6c05739e72dcb1e56aac3662c5965567c9bbb3ad` (16 Apr 2026)

**Disposition:** original estate-owned predecessor to the current Software-Defined Laboratory architecture.

The source project describes a **Cloud GSA Prototype v0.2** for a `1:3:1(+M)` framework:

- one MKS/conservation foundation;
- three domains: KitchenLab, Robot EDU, WalkWise/SQM+;
- one shared Cloud GSA backend;
- a meta/governance layer.

Its stated design intent was a common session grammar and a clear edge -> client -> cloud path, with a small, intelligible runtime and physically interpretable metrics. Those ideas are useful SDL ancestry even though the current architecture no longer treats a cloud backend as the only or mandatory path.

## Snapshot reality

The README in the source repository describes a larger FastAPI prototype with models, metrics, edge simulation, integration tests, schema, architecture notes, and a roadmap. At the inspected source snapshot, however, the Git tree contains only:

- `README.md`;
- a minimal `main.py` FastAPI root endpoint;
- `requirements.txt`;
- `.gitignore`;
- a tiny logo placeholder.

The additional files named by the historical README are not present in that snapshot, so they are not represented here as migrated artifacts.

The surviving Python and dependency files are copied beside this record. The original repository remains intact as provenance.

## Architectural significance

Cloud GSA shows the earlier convergence of KitchenLab, robotics, and WalkWise/SQM+ around common sessions and telemetry. SDL generalizes that idea toward replaceable transports, local or networked hosts, simple endpoints, AI collaboration, and physical experiments without making cloud infrastructure a prerequisite.
