# Sandbox Channel Assignment and Refusal Rules

## The channel is assigned, not chosen

The core names the permitted sandbox server and tool names in the task objective, following the framework's external tools policy. The executor's entire interaction with execution infrastructure happens through that channel:

- Use only the named server and tools. A different tool on the same server is outside the channel.
- The channel identity goes into the environment manifest exactly as assigned.
- No channel at all means no execution: return a blocker stating which protocol steps need which capability. Never fall back to local execution, shell access, or an unlisted server "just for one step".

## Refusal rules

Refuse and return a blocker when:

| Situation | Correct action |
|---|---|
| No server/tool named in the objective | Blocker: execution channel unassigned |
| Named channel lacks a capability a protocol step needs | Blocker naming the step and the missing capability |
| Channel requests credentials or purchases | Blocker; authorization is a user-level decision routed through the core |
| Channel fails or becomes unavailable mid-run | Stop, preserve partials, diagnose in `analysis.md`, blocker |
| A step would broaden permissions (network egress, new endpoints) | Blocker, even if the protocol text loosely permits it |

## Provenance

Every channel interaction leaves a record:

- Query or command, timestamp, and the response identifier where the channel provides one.
- Raw responses preserved under the assigned output path, not summarized away.
- Source URI, retrieval date, and digest where the channel returns external material.

An external channel's output is metadata evidence, not a scientific endorsement. Coverage limits and version drift are recorded as limitations in the run summary.

## Independence from core gates

This skill does not check or grant the experiment gate (`mode=research`, evaluation fields, frozen protocol) - the core's helper enforces those before the task can run. The executor verifies only what it can see: the protocol hash it was given matches the frozen artifact, and the channel it was given covers the steps it must run. Suspected gate violations are reported, not adjudicated.
