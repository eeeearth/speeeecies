"""Run the JavaScript blockmesh regression from the existing pytest workflow."""

import shutil
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
NODE_TEST = REPO_ROOT / "tools" / "tests" / "test_blockmesh.mjs"


def test_blockmesh_renderer_node_regression():
    node = shutil.which("node")
    if node is None:
        pytest.fail(
            "Node.js is required for the blockmesh renderer regression: "
            "node --test tools/tests/test_blockmesh.mjs"
        )

    result = subprocess.run(
        [node, "--test", str(NODE_TEST)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        "blockmesh Node.js regression failed\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )
