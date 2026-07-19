import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_railway_config_preserves_production_contract() -> None:
    config = json.loads((ROOT / "railway.json").read_text())

    assert config["build"]["builder"] == "DOCKERFILE"
    assert config["build"]["dockerfilePath"] == "Dockerfile.railway"

    deploy = config["deploy"]
    assert deploy["healthcheckPath"] == "/api/v1/health"
    assert deploy["healthcheckTimeout"] == 30
    assert deploy["restartPolicyType"] == "ON_FAILURE"
    assert deploy["restartPolicyMaxRetries"] == 10
    assert type(deploy["drainingSeconds"]) is int
    assert deploy["drainingSeconds"] == 10
