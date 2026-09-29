---
name: research-diagram-design
description: Use when supplied system components and relationships need a precise research diagram specification or an artifact rendered by an explicitly assigned backend.
---

# Research Diagram Design

Represent an approved mechanism or architecture accurately. This skill does not choose a model service or compose a research workflow.

## Inputs

Component definitions, relationships, data/control distinctions, approved labels, target size, visual style, assigned renderer if any, output paths and tool limits.

## Method

1. Extract entities and relationships from supplied material. Flag ambiguity instead of inventing components to make the diagram symmetric.
2. Choose layout from the actual structure: left-to-right sequence, hierarchical tree, layered view, or explicit feedback graph. Group details only when meaning is preserved.
3. Specify every node, edge direction, label and legend. Distinguish data flow, control and conditional feedback consistently.
4. Use readable typography, restrained semantic colors and spacing. Validate label fidelity and grayscale/colorblind legibility at final size.
5. Produce a renderer-neutral diagram specification. Render only with the backend explicitly provided by the assignment; if unavailable, return the specification and blocker rather than selecting a service or model.
6. Compare the rendered artifact, if any, with the specification. Generated images are illustrations, not measurement evidence. Report incorrect labels or missing edges.

## Outputs

A component-edge specification, source or prompt appropriate to the assigned backend, optional rendered figure, and a fidelity checklist at assigned paths.

## Checks

No phantom relationships, reversed edges, invented measurements or unsupported causal arrows. Visual emphasis must not alter the mechanism. A design of an agent loop is a picture, not authorization to start that loop.

## Local Reference

[Diagram specification examples](references/diagram-generation.md) provide layout, style, and fidelity techniques. Backend examples are historical; only the core-assigned renderer may be used.

## Boundary

Return to the core with the design or rendering blocker. Do not dispatch other skills or agents, select or switch models, provision services, schedule retries, alter global state, or decide the next research task.
