from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_distribution_name_avoids_reserved_pypi_name_and_keeps_import_package():
    pyproject = (ROOT / "pyproject.toml").read_text()

    assert 'name = "sovereignty-protocol"' in pyproject
    assert '[tool.setuptools.packages.find]' in pyproject
    assert 'where = ["src"]' in pyproject


def test_cli_entrypoint_is_declared_for_installed_package():
    pyproject = (ROOT / "pyproject.toml").read_text()

    assert '[project.scripts]' in pyproject
    assert 'sovereignty = "sovereignty.__main__:main"' in pyproject


def test_build_dependency_and_build_job_are_declared_for_ci():
    pyproject = (ROOT / "pyproject.toml").read_text()
    workflow = (ROOT / ".github" / "workflows" / "tests.yml").read_text()

    assert 'build>=1.0' in pyproject
    assert "python -m build" in workflow


def test_release_checklist_documents_v010_path_and_name_strategy():
    checklist = ROOT / "docs" / "release-checklist.md"

    assert checklist.exists()
    text = checklist.read_text()
    for phrase in [
        "sovereignty-protocol",
        "sovereignty is already taken on PyPI",
        "git tag v0.1.0",
        "python -m build",
        "twine upload",
        "fresh virtual environment",
        "sovereignty --help",
    ]:
        assert phrase in text
