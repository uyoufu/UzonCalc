---
title: Get Started
icon: lightbulb
order: 1
---

## Introduction

UzonCalc is an AI-oriented calculation report authoring tool. Its goal is to let AI help engineers generate and revise calculation reports quickly, so a report can be written once and reused for a long time.

With UzonCalc, you focus on calculation logic. The framework substitutes variables, generates calculation steps, renders mathematical formulas, handles layout, and outputs a professional report document.

UzonCalc reports are written in native Python syntax. There is no separate template language, so it is easy to get started and remains extensible.

## Choose a Workflow

UzonCalc currently supports two primary workflows:

- Windows desktop: for users who manage reports, fill UI inputs, and run reports.
- CLI: for report authors who work with VSCode, AI tools, formatting, linting, and version control.

If you are authoring reports, the CLI workflow is recommended. It is better suited for automatic formatting, syntax checks, version control, and AI-assisted editing.

## Windows Desktop

1. **Download the software**

   Download the `win-x64` package from [Releases · uyoufu/UzonCalc](https://github.com/uyoufu/UzonCalc/releases), unzip it, and run `UzonCalc.exe`.

2. Paste the following code into a new editor:

   ```python
   from uzoncalc import *

   @uzon_calc()
   async def sheet():
       doc_title("example")

       "Hello, UzonCalc!"

       w = 10*unit.m
       l = 5*unit.m
       A = w * l
   ```

3. Click the run button.

   ![UzonCalc run result](https://oss.uzoncloud.com:2234/public/files/images/image-20260527133234259.png)

## CLI

The CLI workflow is mainly for report authors. It works well with editors, AI tools, and code formatters, so reports can be maintained like regular Python projects.

### 1. Install Python

Install Python 3.11 or later and confirm that the command line can run:

```bash
python --version
```

### 2. Install UzonCalc

Install with `pip` or `uv`:

```bash
pip install uzoncalc
```

or:

```bash
uv add uzoncalc
```

### 3. Create a Report Script

Create `example.py`:

```python
# example.py

from uzoncalc import *

@uzon_calc()
async def sheet():
    doc_title("example")

    "Hello, UzonCalc!"

    w = 10*unit.m
    l = 5*unit.m
    A = w * l

if __name__ == "__main__":
    view(sheet)
```

### 4. Run It

Run it as a normal Python script:

```bash
python example.py
```

You will see output like `Serving document at: http://127.0.0.1:32180/`. Open the URL in a browser to view the result.

You can also run it with the UzonCalc CLI:

```bash
uzoncalc example.py
```

When using `python example.py`, the script needs `view(sheet)` at the end. When using `uzoncalc example.py`, the CLI starts the report service for you. During active development, the CLI workflow is recommended because it is better for hot reload and continuous editing.

## First Report Structure

A minimal report usually looks like this:

```python
from uzoncalc import *


@uzon_calc()
async def sheet():
    doc_title("example")

    "Hello, UzonCalc!"

    width = 10 * unit.m
    length = 5 * unit.m
    area = width * length
```

- `from uzoncalc import *` imports common document functions, units, and calculation tools.
- `@uzon_calc()` marks `sheet` as the report entry point.
- Strings are emitted as body paragraphs.
- Assignment statements are recorded as formulas and rendered with substituted values and results.

## Server Deployment

Server deployment documentation will be provided later. For now, use the Windows desktop app or the CLI workflow.

## Docker

Docker deployment documentation will be provided later.
