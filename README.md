# shea

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
