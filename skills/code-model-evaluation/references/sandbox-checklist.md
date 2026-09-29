# Execution Sandbox Checklist

Execution turns generated code into a measurement. An unverified environment supports no correctness claim. This skill does not execute code; use the checklist to audit a supplied execution record or to specify one for a separate authorized task.

## Environment Identity

| Field | Example |
|---|---|
| Language/runtime versions | Python 3.11.4, Node 20.11 |
| Package manifest and lock | `requirements.txt` + lock with hashes |
| Base image or container digest | Image digest, not a floating tag |
| Hardware/CPU/memory limits | 2 vCPU, 4 GB, no GPU |
| Environment variables and locale | `TZ=UTC`, `LC_ALL=C.UTF-8` |

## Isolation and Safety

The isolation and safety controls below apply to any execution record, whether this skill audits it or specifies it for a separate authorized task.

| Control | Requirement |
|---|---|
| Network | Disabled by default; allowlist only when the task explicitly needs it |
| Filesystem | Ephemeral workspace; no access to project state, credentials or raw data |
| Privileges | Unprivileged user; no host mounts |
| Timeouts | Per-test and per-task timeouts with recorded values |
| Resource caps | Memory, CPU time, process count, output size |
| Cleanup | Workspace destroyed after each task; artifacts copied out explicitly |
| Untrusted code policy | Generated code is untrusted input; never run it outside the sandbox |

## Determinism and Classification

- Pin package versions; record any network-dependent test as environment-dependent.
- Distinguish pass, fail, compile error, runtime error, timeout, crash and sandbox violation.
- Re-run flaky tests and record flake rates; a flaky test is an oracle defect, not model variance.
- Record random seeds and any nondeterministic library behavior.
- Log per-task status, duration and exit codes at an assigned path.

## Reporting

| Situation | Wording |
|---|---|
| Full record available | Execution audited against the recorded environment; no independent rerun performed |
| Partial record | Runtime versions unknown; correctness claims unverified |
| No execution | No execution performed; reported values are unverified generated outputs |

Timeouts and sandbox violations are results to be reported, never silently dropped from the denominator.
