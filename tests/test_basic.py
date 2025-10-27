import pytest
from shea.pydisk import _format_bytes, _get_dir_size
from shea.pydisk import main as pydisk_main
from shea.pyls import main


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


# pydisk tests


def test_format_bytes() -> None:
    """Test byte formatting function."""
    assert _format_bytes(0) == "0.0B"
    assert _format_bytes(500) == "500.0B"
    assert _format_bytes(1024) == "1.0KB"
    assert _format_bytes(1024 * 1024) == "1.0MB"
    assert _format_bytes(1024 * 1024 * 1024) == "1.0GB"
    assert _format_bytes(1536) == "1.5KB"  # 1.5 KB
    assert _format_bytes(-100) == "0B"  # Negative values


def test_get_dir_size(tmp_path) -> None:
    """Test directory size calculation."""
    # Create test structure
    file1_size = 5  # "hello"
    file2_size = 5  # "world"
    file3_size = 4  # "test"
    expected_min_size = file1_size + file2_size + file3_size

    (tmp_path / "file1.txt").write_text("hello", encoding="utf-8")
    (tmp_path / "file2.txt").write_text("world", encoding="utf-8")
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    (subdir / "file3.txt").write_text("test", encoding="utf-8")

    # Calculate size
    size = _get_dir_size(tmp_path)

    # Total should be at least expected_min_size bytes
    assert size >= expected_min_size


def test_get_dir_size_with_cache(tmp_path) -> None:
    """Test directory size calculation with caching."""
    # Create test structure
    file1_size = 100
    file2_size = 200
    expected_min_size = file1_size + file2_size

    (tmp_path / "file1.txt").write_text("a" * file1_size, encoding="utf-8")
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    (subdir / "file2.txt").write_text("b" * file2_size, encoding="utf-8")

    cache = {}

    # First call - should populate cache
    size1 = _get_dir_size(tmp_path, cache)
    assert size1 >= expected_min_size
    assert str(tmp_path.resolve()) in cache
    assert str(subdir.resolve()) in cache

    # Second call - should use cache
    size2 = _get_dir_size(tmp_path, cache)
    assert size1 == size2


def test_get_dir_size_skips_symlinks(tmp_path) -> None:
    """Test that symlinks are skipped to avoid infinite loops."""
    file_content = "test"
    expected_min_size = len(file_content)

    (tmp_path / "file.txt").write_text(file_content, encoding="utf-8")

    # Create a symlink that points back to parent (potential infinite loop)
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    try:
        (subdir / "link_to_parent").symlink_to(tmp_path)
    except OSError:
        # Some systems may not support symlinks
        pytest.skip("Symlinks not supported on this system")

    # Should complete without hanging
    size = _get_dir_size(tmp_path)
    assert size >= expected_min_size


def test_pydisk_show_disks(capsys) -> None:
    """Test that pydisk without arguments shows disk information."""
    rc = pydisk_main([])
    assert rc == 0

    out = capsys.readouterr().out
    # Should contain disk icon and some output
    assert "💾" in out or "Disk" in out


def test_pydisk_version_flag(capsys) -> None:
    """Ensure the version is shown when --version is used."""
    with pytest.raises(SystemExit) as e:
        pydisk_main(["--version"])
    assert e.value.code == 0
    out = capsys.readouterr().out
    assert "pydisk" in out


def test_pydisk_nonexistent_path(capsys) -> None:
    """Test pydisk with a non-existent path."""
    rc = pydisk_main(["/nonexistent/path/that/does/not/exist"])
    assert rc == 1

    err = capsys.readouterr().err
    assert "does not exist" in err


def test_pydisk_file_path(tmp_path, capsys) -> None:
    """Test pydisk with a file instead of directory."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("test", encoding="utf-8")

    rc = pydisk_main([str(test_file)])
    assert rc == 1

    err = capsys.readouterr().err
    assert "not a directory" in err
