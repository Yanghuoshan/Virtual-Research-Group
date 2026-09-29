# Third-Party Content and Provenance

## Source and Adaptation

Reused material originated from the public repository https://github.com/Orchestra-Research/AI-Research-SKILLs , installed locally at `../.claude/skills`, outside this repository. The locally installed copy records no upstream revision, so this framework cannot assert which upstream commit its adaptations were derived from. The upstream repository's latest commit when this notice was written (2026-09-29) was `773a529` on `main`, committed 2026-06-16 ("RELEASE: V1.7.2"). Treat that as a reference point only, not as the verified source revision of the adapted files.

The former six knowledge packages now live in the flat `skills/` namespace. Their entry documents have been rewritten as bounded specialists: hypothesis ranking, problem reformulation, ML writing, systems writing, quantitative plotting and talk composition. This is a structural adaptation, not a claim of byte-identical upstream skills.

Citation API references were moved to `citation-verification`; diagram references moved to `research-diagram-design`. Cross-skill redirection and model-selection instructions in affected references were removed or bounded to core-assigned tools. Earlier English-language adaptations remain.

`provenance.json` maps every reused source file that is still present to its current path and records original and current hashes with adaptation notes. It is an integrity and attribution record, not a routing registry; `research.py validate` fails when an adapted file's hash no longer matches. New first-party specialist entries do not need registration there.

## Licensing

The first-party content of this repository is MIT licensed; see [LICENSE](LICENSE).

The upstream project declares MIT for its own material and notes that individual skills may reference libraries with different licenses. Adapted text remains attributed and is not claimed to be an unchanged upstream copy. Entry rewriting does not remove attribution obligations.

Entries whose topics overlap upstream tool documentation (`llm-evaluation`, `code-model-evaluation`, `interpretability-validation`) were written independently for this repository as methodology audits. They contain no copied upstream text and are therefore not recorded in `provenance.json`.

No third-party LaTeX templates are bundled. Conference author kits (ICML, ICLR, NeurIPS, ACL, AAAI, COLM, ASPLOS, NSDI, OSDI, SOSP) must be downloaded from each venue's official source; the links are in the two writing skills. Earlier revisions of this bundle carried copies of those templates, including LPPL-licensed style files such as `natbib.sty`, `fancyhdr.sty`, `algorithm.sty` and `algorithmic.sty`, plus example PDFs. They were removed before publication because their distribution conditions could not be satisfied here. Do not reintroduce them without clearing each license.

## Applicability and Execution

Retained historical API examples, dates, venue requirements and quantitative claims require independent verification. No template was compiled and no research example was run as part of adapting these documents. Reference examples do not authorize installation, external services, model selection, scheduling, submissions or extra research. Specialist execution is bounded by the core's explicit assignment.
