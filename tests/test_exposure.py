from sovereignty import Exposure, SovereigntyPolicyError


def test_exposure_rejects_measured_without_evidence():
    try:
        Exposure(classification="none", trust_model="measured")
    except SovereigntyPolicyError as exc:
        assert "evidence" in str(exc)
    else:
        raise AssertionError("measured exposure must include evidence")


def test_exposure_accepts_caller_attested_without_evidence():
    exposure = Exposure(classification="summary", trust_model="caller_attested")

    assert exposure.classification == "summary"
    assert exposure.trust_model == "caller_attested"
    assert exposure.evidence is None


def test_exposure_rejects_unknown_classification():
    try:
        Exposure(classification="partial", trust_model="caller_attested")
    except SovereigntyPolicyError as exc:
        assert "classification" in str(exc)
    else:
        raise AssertionError("unknown exposure classifications must be rejected")
