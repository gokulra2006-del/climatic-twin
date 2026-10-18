from app.api.api_v1.endpoints.synthetic_benchmark import benchmark_summary


def test_synthetic_benchmark_is_explicitly_non_deployable():
    report = benchmark_summary()
    assert report["provenance"] == "SYNTHETIC_SIMULATION_V1"
    assert report["deployment_policy"] == "BENCHMARK_ONLY_DO_NOT_DEPLOY"
    assert report["generated_rows"] > 3000
    assert "do not establish accuracy" in report["claim_boundary"].lower()
