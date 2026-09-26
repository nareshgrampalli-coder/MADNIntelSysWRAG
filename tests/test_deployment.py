from pathlib import Path
import json


def test_vercel_configuration_declares_api_functions() -> None:
    config = json.loads(Path("vercel.json").read_text(encoding="utf-8"))

    assert "api/*.py" in config["functions"]
    assert Path("api/health.py").exists()
    assert Path("DEPLOYMENT.md").exists()
