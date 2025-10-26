import pytest
from shea.main import main


def test_main_runs(tmp_path, capsys) -> None:
    """Ensure main runs without error on a simple directory."""
    # Arrange a temporary directory with some content
    (tmp_path / "sub").mkdir()
    (tmp_path / "file.txt").write_text("hello\n", encoding="utf-8")

    # Flat listing
    rc = main([str(tmp_path)])
    assert rc == 0

    # Tree view with depth
    rc = main(["--tree", "--depth", "2", str(tmp_path)])
    assert rc == 0

    # Output contains at least one icon
    out = capsys.readouterr().out
    assert "📁" in out or "📄" in out


def test_version_flag(capsys) -> None:
    """Ensure the version is shown when --version is used."""
    with pytest.raises(SystemExit) as e:
        main(["--version"])  # argparse's version action prints and exits with code 0
    assert e.value.code == 0
    out = capsys.readouterr().out
    assert out.strip().startswith("shea ")
