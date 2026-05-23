from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "shadow-lane-evaluation.md"


def test_shadow_lane_doc_defines_evaluation_only_boundary():
    text = DOC.read_text()

    for phrase in [
        "evaluation-only",
        "must never affect final answer or side effects",
        "metadata-only",
        "quality",
        "latency",
        "classifier",
        "writer",
        "extractor",
        "packet telemetry",
        "lane health",
    ]:
        assert phrase in text
