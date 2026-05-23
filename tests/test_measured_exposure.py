from sovereignty import RecordedRequest, build_measured_exposure_report


LOCAL_INPUT = "Revenue is down 17% in the private board packet."


def test_measured_report_classifies_no_cloud_requests_as_none():
    report = build_measured_exposure_report(
        local_input=LOCAL_INPUT,
        observed_requests=[],
        verifier_id="test-recorder",
    )

    assert report["schema_version"] == "0.1"
    assert report["trust_model"] == "measured"
    assert report["verifier_id"] == "test-recorder"
    assert report["classification"] == "none"
    assert report["observed_request_count"] == 0
    assert report["transmitted_byte_count"] == 0
    assert report["evidence"]["request_digests"] == []
    assert "raw request bodies are not included" in report["limitations"]


def test_measured_report_classifies_exact_input_transmission_as_raw_without_leaking_body():
    report = build_measured_exposure_report(
        local_input=LOCAL_INPUT,
        observed_requests=[
            RecordedRequest(
                method="POST",
                url="https://api.example.invalid/v1/chat/completions",
                body=f"please summarize: {LOCAL_INPUT}".encode(),
            )
        ],
        verifier_id="test-recorder",
    )

    assert report["classification"] == "raw"
    assert report["observed_request_count"] == 1
    assert report["transmitted_byte_count"] > len(LOCAL_INPUT)
    assert report["evidence"]["request_digests"][0].startswith("sha256:")
    assert "api.example.invalid" not in str(report)
    assert LOCAL_INPUT not in str(report)


def test_measured_report_classifies_partial_input_transmission_as_excerpt():
    report = build_measured_exposure_report(
        local_input=LOCAL_INPUT,
        observed_requests=[
            RecordedRequest(
                method="POST",
                url="https://api.example.invalid/v1/chat/completions",
                body=b"The private board packet says revenue is down 17%.",
            )
        ],
    )

    assert report["classification"] == "excerpt"


def test_measured_report_classifies_unmatched_nonempty_requests_as_unknown():
    report = build_measured_exposure_report(
        local_input=LOCAL_INPUT,
        observed_requests=[
            RecordedRequest(
                method="POST",
                url="https://api.example.invalid/v1/chat/completions",
                body=b"A heavily paraphrased analysis went here.",
            )
        ],
    )

    assert report["classification"] == "unknown"
    assert "semantic equivalence is not proven" in report["limitations"]
