# SUPER SDL Versioning Policy

SUPER SDL uses independent semantic versions for independently evolving boundaries.
Do not infer compatibility merely because two component numbers are similar.

## v0.6.0 release matrix

| Item | Version | Compatibility role |
|---|---:|---|
| SUPER SDL complete release | 0.6.0 | release bundle identity |
| Pico runtime | 0.6.0 | embedded implementation |
| PC Gateway | 0.6.0 | Windows implementation |
| SDL Traffic Cop | 1.2.0 | passive monitor implementation |
| SDL ASCII Protocol | 1.0.0 | **PC ↔ Pico wire contract** |
| Capability API | 1.0.0 | **Pico extension contract** |
| MCP protocol target | 2026-07-28 | **Codex/client ↔ PC Gateway contract** |
| Newton cooling reference capability | 0.3.0 | example late-bound package |

## Compatibility rules

1. The Gateway refuses a Pico that does not report SDL ASCII Protocol `1.0.0`.
2. The Gateway refuses a Pico that does not report Capability API `1.0.0`.
3. Pico runtime patch/minor releases may differ from the Gateway release when the two stable contracts above remain compatible.
4. Traffic Cop is out-of-band and may evolve independently. It must never be a required control dependency.
5. A breaking SDL wire change increments the SDL protocol major version.
6. A breaking capability registration/manifest change increments the Capability API major version.
7. Release ZIP names always contain their version and every ZIP contains a `VERSION`, `BUILD.json`, and SHA-256 manifest.

## Startup identity

The Pico exposes `INFO`/`VERSION`; the Gateway checks it before publishing MCP.
A representative identity is:

```text
runtime=0.6.0
protocol=1.0.0
capabilityApi=1.0.0
```

This is intentional: incompatible software should fail loudly at startup rather than produce ambiguous laboratory behavior.
