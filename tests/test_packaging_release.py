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


def test_pypi_publish_workflow_uses_trusted_publishing_not_stored_tokens():
    workflow = ROOT / ".github" / "workflows" / "publish.yml"

    assert workflow.exists()
    text = workflow.read_text()
    for phrase in [
        "id-token: write",
        "pypa/gh-action-pypi-publish@release/v1",
        "environment: pypi",
        "environment: testpypi",
        "repository-url: https://test.pypi.org/legacy/",
        "workflow_dispatch",
        "release:",
        "types: [published]",
    ]:
        assert phrase in text

    forbidden_phrases = [
        "TWINE_PASSWORD",
        "TWINE_USERNAME",
        "__token__",
        "password:",
        "api-token",
    ]
    for phrase in forbidden_phrases:
        assert phrase not in text


def test_release_checklist_documents_trusted_publishing_setup():
    text = (ROOT / "docs" / "release-checklist.md").read_text()

    for phrase in [
        "Trusted Publishing",
        "environment name `pypi`",
        "environment name `testpypi`",
        ".github/workflows/publish.yml",
        "no Twine API token",
        "workflow_dispatch",
    ]:
        assert phrase in text
