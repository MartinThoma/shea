# pyl

A simple Python directory lister with an optional tree view, similar to ls and tree.

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

List current directory (folders first, then files):

```bash
pyl
```

Tree view:

```bash
pyl -t
```

Specify a path and a maximum depth:

```bash
pyl --tree --depth 2 ~/projects
```

### Output examples

Listing:

```
📁 src
📄 README.md
📄 pyproject.toml
```

Tree view:

```
.
├── src
│   ├── pyl
│   │   ├── __init__.py
│   │   └── main.py
│   └── pyproject.toml
└── README.md
```

## Python compatibility

Python 3.8+

## License

MIT

## Pre-commit (Ruff)

This repo includes a pre-commit configuration to run Ruff for linting and formatting.

Install and enable it:

```bash
python -m pip install pre-commit
pre-commit install
```

Run on all files once:

```bash
pre-commit run -a
```

Ruff lint will auto-fix simple issues on commit; if it makes changes, the commit will fail so you can review and re-commit.
