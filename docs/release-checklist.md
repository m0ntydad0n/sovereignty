# Release checklist

Sovereignty v0.1.0 is the first installable protocol release. The repository
name remains `sovereignty`, and the import package and CLI command remain
`sovereignty`, but the Python distribution name is `sovereignty-protocol`.

## Package name strategy

sovereignty is already taken on PyPI, so the v0.1.0 package should publish as
`sovereignty-protocol` unless the project later obtains the canonical name. This
keeps the public API simple:

```bash
python -m pip install sovereignty-protocol
python -c "import sovereignty; print(sovereignty.__version__)"
sovereignty --help
```

## Pre-release verification

1. Start from a clean tree on `main`.
2. Confirm tests pass:

   ```bash
   python -m pytest tests -q
   ```

3. Build source distribution and wheel:

   ```bash
   python -m build
   ```

4. Check package metadata:

   ```bash
   python -m twine check dist/*
   ```

5. Install the built wheel into a fresh virtual environment and verify import and
   CLI behavior without `PYTHONPATH=src`:

   ```bash
   tmpdir=$(mktemp -d)
   python3 -m venv "$tmpdir/venv"
   "$tmpdir/venv/bin/python" -m pip install --upgrade pip
   "$tmpdir/venv/bin/python" -m pip install dist/sovereignty_protocol-0.1.0-py3-none-any.whl
   "$tmpdir/venv/bin/python" -c "import sovereignty; print(sovereignty.__version__)"
   "$tmpdir/venv/bin/sovereignty" --help
   rm -rf "$tmpdir"
   ```

## Tag and publish

1. Create and push the release tag:

   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```

2. Configure PyPI/TestPyPI Trusted Publishing for `.github/workflows/publish.yml`.
   Use no Twine API token in GitHub secrets or local files when trusted publishing is available.

   Required publisher settings:

   - owner/repository: `m0ntydad0n/sovereignty`
   - workflow file: `.github/workflows/publish.yml`
   - environment name `testpypi` for TestPyPI
   - environment name `pypi` for PyPI
   - package/project name: `sovereignty-protocol`

3. Publish to TestPyPI first from GitHub Actions:

   - open the `Publish Python package` workflow;
   - run `workflow_dispatch` with repository `testpypi`;
   - verify the `testpypi` environment is used;
   - verify fresh install/import/CLI from TestPyPI.

4. Publish to PyPI after TestPyPI install/import/CLI verification:

   - publish a GitHub release, or run `workflow_dispatch` with repository `pypi`;
   - verify the `pypi` environment is used;
   - verify fresh install/import/CLI from PyPI.

5. Manual fallback only if trusted publishing cannot be configured:

   ```bash
   python -m twine upload --repository testpypi dist/*
   python -m twine upload dist/*
   ```

   Use scoped, project-specific credentials only; do not commit `.pypirc`, tokens, or local credential files.

6. Create the GitHub release for `v0.1.0` with notes that call out:
   - review packet validation;
   - metadata redaction;
   - measured exposure reports and recording boundary;
   - side-effect proposal schema;
   - JSON Schema contracts;
   - Hermes/local-router examples.

## Post-release verification

Use a fresh virtual environment, install from PyPI, and verify:

```bash
python3 -m venv /tmp/sovereignty-v010-check
/tmp/sovereignty-v010-check/bin/python -m pip install --upgrade pip
/tmp/sovereignty-v010-check/bin/python -m pip install sovereignty-protocol==0.1.0
/tmp/sovereignty-v010-check/bin/python -c "import sovereignty; print(sovereignty.__version__)"
/tmp/sovereignty-v010-check/bin/sovereignty --help
```
