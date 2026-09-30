# Framework and Flow Diagrams

One-page visual contract of the framework. Text remains authoritative; these diagrams orient new readers and serve as the map when navigating [the core contract](../SKILL.md), [operations](operations.md), and the [host bridge](host-bridge.md).

## 1. Framework architecture

Three layers with strict downward dependencies: the core decides, specialists execute bounded tasks, and the host provides execution resources and supervision. Nothing in a lower layer writes upward.

```mermaid
graph TD
    subgraph CORE["Core decision layer (one agent, sole state writer)"]
        COREDOC[SKILL.md core contract]
        STATE[(research-state.json<br/>phase, tasks, gates, history)]
        BRIEF[research-log.md<br/>current brief + narrative]
        FIND[findings.md]
    end

    subgraph HELPER["Deterministic helper (scripts/research.py)"]
        CMD[15 explicit core commands<br/>task / handoff / accept / task-status / phase<br/>authorize / set-evaluation / set-protocol / set-audit<br/>blockers / project-status / init / validate / skills / status<br/>4 read-only: handoff, validate, skills, status]
    end

    subgraph SPEC["Specialist skills (flat, one task each)"]
        IDEATE[ideation and review<br/>brainstorming, literature-review,<br/>citation-verification]
        DESIGN[design and audit<br/>experimental-design, reproducibility-audit,<br/>evaluation skills]
        EXECUTE[execution<br/>experiment-execution]
        DATA[data layer<br/>data-processing, statistical-analysis]
        COMMUNICATE[communication<br/>paper-writing, plotting, talks]
    end

    subgraph HOST["Host layer"]
        SUB[isolated subagent sessions<br/>execute one packet each]
        WATCH[watchdog automation<br/>read-only anomaly reports]
        HUMAN([human supervisor<br/>reads brief, intervenes])
    end

    COREDOC --> CMD
    CMD -->|atomic writes, revision, history| STATE
    COREDOC -->|saves packets and receipts| HANDOFFS[handoffs/ packets + receipts]
    COREDOC -->|one skill per assignment| SPEC
    SUB -->|writes artifacts| WS[(project workspace<br/>experiments/ runs, data/, paper/)]
    SPEC -->|artifacts and blockers| CORE
    WATCH -->|reads state and brief| STATE
    WATCH -->|anomaly report| HUMAN
    BRIEF -->|primary progress window| HUMAN
    HUMAN -->|approval, intervention| CORE
```

Key invariants visible in the diagram:

- Only the core writes `research-state.json`, `research-log.md`, `findings.md` and `handoffs/`.
- The helper implements core decisions; it dispatches nothing and schedules nothing.
- Specialists never call each other, never spawn agents, never touch global state.
- The watchdog only reads; it reports to the human, never to the loop.

## 2. Research flow across phases

Phases are goals with exit criteria, not a task pipeline; each phase holds multiple tasks. Only a separate core `phase` decision moves the project between them.

```mermaid
stateDiagram-v2
    [*] --> scope
    scope --> ideation: question bounded
    ideation --> design: hypothesis selected
    ideation --> scope: scope must change
    design --> execute: protocol frozen
    design --> ideation: redesign justified
    execute --> synthesize: evidence sufficient
    execute --> design: redesign justified
    synthesize --> write: assessment stable
    synthesize --> ideation: new direction justified
    synthesize --> design: sharper test needed
    write --> review: draft traceable
    write --> synthesize: evidence gaps
    review --> complete: audits passed
    review --> write: issues routed back
    review --> design: validity flaw
    review --> synthesize: claim overreach
    complete --> scope: reopened by a new core decision
    scope --> [*]
```

## 3. Evidence pipeline (the closed loop)

The chain that makes automated research trustworthy: every claim binds back to frozen protocol and raw evidence through checksums and audits.

```mermaid
graph LR
    H[hypothesis] --> P[experimental-design<br/>draft protocol]
    P -->|core freezes| F[frozen protocol<br/>hash recorded]
    F -->|experiment gate<br/>mode + evaluation fields| E[experiment-execution<br/>runs in assigned sandbox]
    E --> R[raw results<br/>runs/run-id/results]
    R --> D[data-processing<br/>clean, validate, manifest]
    D --> M[data manifest<br/>checksums, drop reasons]
    M --> S[statistical-analysis<br/>pre-specified tests only]
    S --> T[summary tables<br/>confirmatory vs exploratory]
    T --> A[academic-plotting<br/>figures]
    R --> AUD[evidence audit<br/>subjects = path + sha256]
    M --> AUD
    T --> AUD
    AUD -->|verified| FIN[findings.md<br/>accepted claims]
    FIN -->|final review + manuscript audit| COMP[phase complete]
```

Gates along the chain: the experiment gate (`authorize` + `set-evaluation` + `set-protocol`) guards execution; the verified evidence audit guards any `conclusions` activity; a final review audit guards `phase --to complete`.

## 4. Host bridge execution loop

One iteration per assignment attempt, with human intervention points marked.

```mermaid
sequenceDiagram
    participant C as Core (one agent)
    participant H as Host facility
    participant X as Isolated subagent session
    participant W as Human supervisor
    C->>C: 1. handoff → packet saved under handoffs/<br/>brief rewritten (INTERVENTION POINT)
    C->>H: 2. spawn subagent with minimal context<br/>(packet + one skill + evidence paths)
    H->>X: fresh / reuse / current session per policy
    X->>X: 3. execute bounded task,<br/>write artifacts in assigned scope
    X-->>C: fill receipt from actual facts<br/>(session id, model, accepted_at, checks)
    C->>C: 4. verify + accept → task running<br/>brief rewritten (INTERVENTION POINT)
    X-->>C: artifacts returned, executor stopped
    C->>C: task-status submitted<br/>inspect artifacts
    C->>C: task-status completed or rework (INTERVENTION POINT)
    W-->>C: any time: blockers / task-status / project-status
    Note over W: watchdog (not shown) reads state and brief<br/>on a schedule and reports anomalies only
```

## 5. Watchdog supervision

```mermaid
graph TD
    TIMER[host schedule fires<br/>every 30-60 min] --> READ[read research-state.json<br/>research-log.md brief, handoffs/]
    READ --> C1{running task silent<br/>> 2h?}
    READ --> C2{receipt stall<br/>> 6h?}
    READ --> C3{blocker age<br/>> 24h?}
    READ --> C4{brief drift vs state?}
    READ --> C5{project silent<br/>> 48h?}
    C1 -- no --> OK[heartbeat: one line, OK]
    C2 -- no --> OK
    C3 -- no --> OK
    C4 -- no --> OK
    C5 -- no --> OK
    C1 -- yes --> REPORT[anomaly report to human:<br/>task id, evidence, suggested action]
    C2 -- yes --> REPORT
    C3 -- yes --> REPORT
    C4 -- yes --> REPORT
    C5 -- yes --> REPORT
    REPORT --> DECIDE{human or core intervenes<br/>via blockers / task-status / project-status}
    DECIDE --> READ
    style REPORT fill:#fdd
    style OK fill:#dfd
```

The watchdog never writes, never dispatches, and never decides - it only makes silence visible.
