from __future__ import annotations

import json
from pathlib import Path


root = Path(__file__).resolve().parents[1] / "apps" / "web"
required = [
    root / "index.html",
    root / "app.js",
    root / "style.css",
    root / "product-manifest.json",
]
missing = [str(path) for path in required if not path.exists()]
assert not missing, f"missing static files: {missing}"

html = (root / "index.html").read_text(encoding="utf-8")
assert 'src="app.js"' in html, "app.js must stay relative for subpath deployment"
assert 'href="style.css"' in html, "style.css must stay relative for subpath deployment"
assert 'src="/app.js"' not in html
assert 'href="/style.css"' not in html

js = (root / "app.js").read_text(encoding="utf-8")
for token in [
    "ANSWER_SUBMITTED",
    "VERIFY_ANSWER",
    "WORD_ANSWER",
    "crypto.randomUUID",
    "CLOSED LOOP",
    "product-manifest.json",
    "homePage",
    "todayPage",
    "labPage",
    "repairPage",
    "topologyPage",
    "assetsPage",
    "profilePage",
]:
    assert token in js, f"missing frontend contract token: {token}"

for forbidden in [
    "fetch('/product-manifest.json'",
    "api('/api/",
    "api(`/api/",
]:
    assert forbidden not in js, f"root-absolute frontend URL breaks subpath deploy: {forbidden}"

for required_relative in [
    "fetch('product-manifest.json'",
    "api('api/v1/session/start'",
    "api('api/v1/learning/step'",
    "api(`api/v1/session/",
]:
    assert required_relative in js, f"missing subpath-safe frontend URL: {required_relative}"

manifest = json.loads((root / "product-manifest.json").read_text(encoding="utf-8"))
assert manifest["version"] == "3.0"
contract = manifest["contract"]
assert contract["prd_version"] == "3.0"
assert contract["preview_can_mutate_learning_state"] is False
assert contract["shell_pages"] == [
    "home",
    "today",
    "lab",
    "repair",
    "topology",
    "assets",
    "profile",
]

capabilities = {
    item["id"]: item
    for group in manifest["groups"]
    for item in group["capabilities"]
}
expected_status = {
    "mece_structure": "preview",
    "word_logic": "limited",
    "sentence_formula": "live",
    "five_whys": "preview",
    "instruction_flow": "preview",
    "physical_restore": "preview",
    "error_diagnosis": "limited",
    "triple_patch": "live",
    "logic_puzzle": "preview",
    "baseline_diagnostic": "preview",
}
assert set(capabilities) == set(expected_status)
for capability_id, status in expected_status.items():
    assert capabilities[capability_id]["status"] == status

allowed_runtime_nodes = set(contract["allowed_runtime_nodes"])
assert allowed_runtime_nodes == {"relative_clause.pointer", "word.root.rupt"}
for capability in capabilities.values():
    if capability["status"] == "preview":
        assert "action" not in capability
        assert "node" not in capability
    if capability.get("action") in {"gold_loop", "repair"}:
        assert capability["status"] in {"live", "limited"}
        assert capability["node"] in allowed_runtime_nodes

runtime_topology_nodes = {
    item["id"] for item in manifest["topology"] if item["status"] == "runtime"
}
assert runtime_topology_nodes == allowed_runtime_nodes

asset_status = {item["id"]: item["status"] for item in manifest["assets"]}
assert asset_status == {
    "error_archive": "limited",
    "repair_log": "live",
    "learning_history": "live",
    "component_library": "limited",
    "learning_report": "preview",
}

assert set(manifest["profile"]) == {
    "learning_goal",
    "content_version",
    "learning_settings",
    "data_privacy",
}

print("STATIC_H5_V3_OK")
