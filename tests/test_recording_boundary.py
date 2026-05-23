from sovereignty import RecordingBoundary, RecordedRequest


LOCAL_INPUT = "Board packet says revenue is down 17%."


def test_recording_boundary_observes_request_before_transport_and_returns_response():
    seen_by_transport = []

    def fake_transport(method: str, url: str, body: bytes):
        seen_by_transport.append((method, url, body))
        return {"status": 200, "body": b"ok"}

    boundary = RecordingBoundary(local_input=LOCAL_INPUT, transport=fake_transport)

    response = boundary.request(
        "POST",
        "https://api.example.invalid/v1/chat/completions",
        f"summarize: {LOCAL_INPUT}".encode(),
    )

    assert response == {"status": 200, "body": b"ok"}
    assert seen_by_transport == [
        (
            "POST",
            "https://api.example.invalid/v1/chat/completions",
            f"summarize: {LOCAL_INPUT}".encode(),
        )
    ]
    assert boundary.observed_requests == [
        RecordedRequest(
            method="POST",
            url="https://api.example.invalid/v1/chat/completions",
            body=f"summarize: {LOCAL_INPUT}".encode(),
        )
    ]


def test_recording_boundary_report_omits_raw_body_and_hostname():
    def fake_transport(method: str, url: str, body: bytes):
        return {"status": 200}

    boundary = RecordingBoundary(local_input=LOCAL_INPUT, transport=fake_transport)
    boundary.request(
        "POST",
        "https://api.example.invalid/v1/chat/completions",
        f"summarize: {LOCAL_INPUT}".encode(),
    )

    report = boundary.report()
    rendered = str(report)

    assert report["classification"] == "raw"
    assert report["observed_request_count"] == 1
    assert report["evidence"]["request_digests"][0].startswith("sha256:")
    assert LOCAL_INPUT not in rendered
    assert "api.example.invalid" not in rendered
    assert "chat/completions" not in rendered


def test_recording_boundary_can_drop_raw_bodies_after_report():
    def fake_transport(method: str, url: str, body: bytes):
        return {"status": 200}

    boundary = RecordingBoundary(local_input=LOCAL_INPUT, transport=fake_transport)
    boundary.request("POST", "https://api.example.invalid/v1/chat/completions", b"body")

    report = boundary.report(drop_observed_bodies=True)

    assert report["observed_request_count"] == 1
    assert boundary.observed_requests == [
        RecordedRequest(
            method="POST",
            url="https://api.example.invalid/v1/chat/completions",
            body=b"",
        )
    ]
