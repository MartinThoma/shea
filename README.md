# shea

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Code style: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

**Shea** (short for "**she**ll **a**pps") is a collection of modern Python-based shell utilities with colorful emoji icons. Currently includes:
- **`pyls`** - Directory listing with tree view (ls/tree replacement)
- **`pytop`** - Process viewer sorted by CPU/memory usage (top/htop alternative)

## Installation

You can install with pip (PEP 517 using Flit under the hood):

```bash
pip install .
```

Or directly with Flit:

```bash
python -m pip install flit
flit install
```

## Usage

### Directory Listing (pyls)

List current directory (folders first, then files):

```bash
shea
```

Tree view:

```bash
shea -t
```

Specify a path and a maximum depth:

```bash
shea --tree --depth 2 ~/projects
```

### Process Viewer (pytop)

Launch the interactive process monitor:

```bash
pytop
```

Features:
- 🔥 Real-time CPU usage per core with visual bars
- 💾 Memory and swap usage with color-coded horizontal charts
- ⚙️ System information (uptime, process count)
- 📊 Process table showing top 50 processes by CPU usage
- 🔄 Click column headers to sort (CPU/MEM/TIME always descending, others toggle)
- Interactive TUI interface with live updates

Controls:
- `q` - Quit
- `r` - Force refresh
- Arrow keys - Navigate process list
- Click column headers - Sort by that column

### Output examples

Listing:

```
$ pyls
📁 dist
📁 shea
📁 tests
📄 pyproject.toml
📄 README.md

```

Tree view:

```
$ pyls -t
.
├── 📁 dist
│   ├── 📄 pyl-0.1.0-py3-none-any.whl
│   ├── 📄 pyl-0.1.0.tar.gz
│   ├── 📄 qwe-0.1.0-py3-none-any.whl
│   ├── 📄 qwe-0.1.0.tar.gz
│   ├── 📄 shea-0.1.0-py3-none-any.whl
│   ├── 📄 shea-0.1.0.tar.gz
│   ├── 📄 shea-0.1.1-py3-none-any.whl
│   └── 📄 shea-0.1.1.tar.gz
├── 📁 shea
│   ├── 📁 __pycache__
│   │   ├── 📄 __init__.cpython-310.pyc
│   │   ├── 📄 __main__.cpython-310.pyc
│   │   ├── 📄 _version.cpython-310.pyc
│   │   ├── 📄 main.cpython-310.pyc
│   │   └── 📄 pyls.cpython-310.pyc
│   ├── 📄 __init__.py
│   ├── 📄 __main__.py
│   ├── 📄 _version.py
│   └── 📄 pyls.py
├── 📁 tests
│   ├── 📁 __pycache__
│   │   └── 📄 test_basic.cpython-310-pytest-8.3.2.pyc
│   └── 📄 test_basic.py
├── 📄 pyproject.toml
└── 📄 README.md
```

## License

MIT

## Development

This project uses [pre-commit](https://pre-commit.com/) with [Ruff](https://github.com/astral-sh/ruff) for linting and formatting.

To set up pre-commit hooks:

```bash
python -m pip install pre-commit
pre-commit install
```

Run on all files once:

```bash
pre-commit run -a
```

Ruff lint will auto-fix simple issues on commit; if it makes changes, the commit will fail so you can review and re-commit.
