# LaTeX Templates for ML/AI Conferences

This directory contains official LaTeX templates for major machine learning and AI conferences.

Systems templates are outside this package. Return a scope mismatch or missing template to the core; do not select another skill.

## Compiling LaTeX to PDF

### Option 1: VS Code with LaTeX Workshop (Recommended)

**Prerequisites:** use an already available toolchain explicitly assigned by the core. If TeX or editor integration is missing, return manuscript source and a dependency blocker; do not install or configure tools as part of writing.

**Usage:**
- Open any `.tex` file in VS Code
- Save the file (Cmd/Ctrl+S) → Auto-compiles to PDF
- Click the green play button or use `Cmd/Ctrl+Alt+B` to build
- View PDF: Click "View LaTeX PDF" icon or `Cmd/Ctrl+Alt+V`
- Side-by-side view: `Cmd/Ctrl+Alt+V` then drag tab

**Example settings** (reference for an already configured host; do not change host configuration in this task):
```json
{
  "latex-workshop.latex.autoBuild.run": "onSave",
  "latex-workshop.view.pdf.viewer": "tab",
  "latex-workshop.latex.recipes": [
    {
      "name": "pdflatex → bibtex → pdflatex × 2",
      "tools": ["pdflatex", "bibtex", "pdflatex", "pdflatex"]
    }
  ]
}
```

### Option 2: Command Line

```bash
# Basic compilation
pdflatex main.tex

# With bibliography (full workflow)
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex

# Using latexmk (handles dependencies automatically)
latexmk -pdf main.tex

# Use one-shot compilation only; do not start a background watcher.
```

### Option 3: Overleaf (Online)

[Overleaf](https://www.overleaf.com) is an external editor, not a default destination. Upload research material only when the core assignment explicitly permits that service and data transfer. Otherwise return local source files.

### Option 4: Other IDEs

| IDE | Extension/Plugin | Notes |
|-----|------------------|-------|
| **Cursor** | LaTeX Workshop | Same as VS Code |
| **Sublime Text** | LaTeXTools | Popular, well-maintained |
| **Vim/Neovim** | VimTeX | Powerful, keyboard-driven |
| **Emacs** | AUCTeX | Comprehensive LaTeX environment |
| **TeXstudio** | Built-in | Dedicated LaTeX IDE |
| **Texmaker** | Built-in | Cross-platform LaTeX editor |

### Troubleshooting Compilation

**"File not found" errors:**
```bash
# Ensure you're in the template directory
cd templates/icml2026
pdflatex example_paper.tex
```

**Bibliography not appearing:**
```bash
# Run bibtex after first pdflatex
pdflatex main.tex
bibtex main        # Uses main.aux to find citations
pdflatex main.tex  # Incorporates bibliography
pdflatex main.tex  # Resolves references
```

**Missing packages:** report the package name and compilation diagnostic to the core. Do not install dependencies or expand the task.

## Available Templates

### ML/AI Conferences / ML/AI 

| Conference | Directory | Year | Source |
|------------|-----------|------|--------|
| ICML | `icml2026/` | 2026 | [Official ICML](https://icml.cc/Conferences/2026/AuthorInstructions) |
| ICLR | `iclr2026/` | 2026 | [Official GitHub](https://github.com/ICLR/Master-Template) |
| NeurIPS | `neurips2025/` | 2025 | Community template |
| ACL | `acl/` | 2025+ | [Official ACL](https://github.com/acl-org/acl-style-files) |
| AAAI | `aaai2026/` | 2026 | [AAAI Author Kit](https://aaai.org/authorkit26/) |
| COLM | `colm2025/` | 2025 | [Official COLM](https://github.com/COLM-org/Template) |

### Systems Conferences

Systems-specific template requirements must be supplied by the core in a separate assignment.

## Usage

### ICML 2026

```latex
\documentclass{article}
\usepackage{icml2026}  % For submission
% \usepackage[accepted]{icml2026}  % For camera-ready

\begin{document}
% Your paper content
\end{document}
```

Key files:
- `icml2026.sty` - Style file
- `icml2026.bst` - Bibliography style
- `example_paper.tex` - Example document

### ICLR 2026

```latex
\documentclass{article}
\usepackage[submission]{iclr2026_conference}  % For submission
% \usepackage[final]{iclr2026_conference}  % For camera-ready

\begin{document}
% Your paper content
\end{document}
```

Key files:
- `iclr2026_conference.sty` - Style file
- `iclr2026_conference.bst` - Bibliography style
- `iclr2026_conference.tex` - Example document

### ACL Venues (ACL, EMNLP, NAACL)

```latex
\documentclass[11pt]{article}
\usepackage[review]{acl}  % For review
% \usepackage{acl}  % For camera-ready

\begin{document}
% Your paper content
\end{document}
```

Key files:
- `acl.sty` - Style file
- `acl_natbib.bst` - Bibliography style
- `acl_latex.tex` - Example document

### AAAI 2026

```latex
\documentclass[letterpaper]{article}
\usepackage[submission]{aaai2026}  % For submission
% \usepackage{aaai2026}  % For camera-ready

\begin{document}
% Your paper content
\end{document}
```

Key files:
- `aaai2026.sty` - Style file
- `aaai2026.bst` - Bibliography style

### COLM 2025

```latex
\documentclass{article}
\usepackage[submission]{colm2025_conference}  % For submission
% \usepackage[final]{colm2025_conference}  % For camera-ready

\begin{document}
% Your paper content
\end{document}
```

Key files:
- `colm2025_conference.sty` - Style file
- `colm2025_conference.bst` - Bibliography style

## Page Limits Summary

| Conference | Submission | Camera-Ready | Notes |
|------------|-----------|--------------|-------|
| ICML 2026 | 8 pages | 9 pages | +unlimited refs/appendix |
| ICLR 2026 | 9 pages | 10 pages | +unlimited refs/appendix |
| NeurIPS 2025 | 9 pages | 9 pages | +checklist outside limit |
| ACL 2025 | 8 pages (long) | varies | +unlimited refs/appendix |
| AAAI 2026 | 7 pages | 8 pages | +unlimited refs/appendix |
| COLM 2025 | 9 pages | 10 pages | +unlimited refs/appendix |

**Systems conferences:** report missing rules or templates to the core instead of redirecting work.

## Common Issues

### Compilation Errors

1. **Missing packages**: Return the missing-package diagnostic to the core.
2. **Bibliography errors**: Use the provided `.bst` file with `\bibliographystyle{}`
3. **Font warnings**: Use only an available, venue-compatible font configuration; otherwise report the missing font.

### Anonymization

For submission, ensure:
- No author names in `\author{}`
- No acknowledgments section
- No grant numbers
- Use anonymous repositories
- Cite own work in third person

### Common LaTeX Packages

```latex
% Recommended packages (check compatibility with venue style)
\usepackage{amsmath,amsthm,amssymb}  % Math
\usepackage{graphicx}                 % Figures
\usepackage{booktabs}                 % Tables
\usepackage{hyperref}                 % Links
\usepackage{algorithm,algorithmic}    % Algorithms
\usepackage{natbib}                   % Citations
```

## Updating Templates

Templates are updated annually. Check official sources before each submission:
**ML/AI:**
- ICML: https://icml.cc/
- ICLR: https://iclr.cc/
- NeurIPS: https://neurips.cc/
- ACL: https://github.com/acl-org/acl-style-files
- AAAI: https://aaai.org/
- COLM: https://colmweb.org/

**Systems:** outside this template package; the core decides any follow-up assignment.
