from app.api.api_v1.endpoints.research_readiness import get_research_readiness


def test_readiness_report_preserves_claim_boundaries():
    report = get_research_readiness(db=None)
    assert report["title"] == "ClimateTwin research evidence readiness"
    assert len(report["items"]) == 9
    drought = next(item for item in report["items"] if item["gap"] == "2019 drought replay")
    assert drought["status"] == "PARTIAL"
    assert "proxy" in drought["claim_boundary"].lower()
