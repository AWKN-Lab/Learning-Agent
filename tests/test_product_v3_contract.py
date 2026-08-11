from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "apps" / "web" / "product-manifest.json"
PRD_PATH = ROOT / "docs" / "PRD.md"


def load_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def capability_index(manifest: dict) -> dict[str, dict]:
    return {
        capability["id"]: capability
        for group in manifest["groups"]
        for capability in group["capabilities"]
    }


def test_v3_shell_contract_is_explicit() -> None:
    manifest = load_manifest()
    contract = manifest["contract"]

    assert manifest["version"] == "3.0"
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
    assert set(contract["allowed_runtime_nodes"]) == {
        "relative_clause.pointer",
        "word.root.rupt",
    }


def test_v3_capability_matrix_matches_prd() -> None:
    manifest = load_manifest()
    capabilities = capability_index(manifest)

    expected = {
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

    assert set(capabilities) == set(expected)
    assert {key: capabilities[key]["status"] for key in expected} == expected


def test_preview_capabilities_cannot_enter_learning_runtime() -> None:
    manifest = load_manifest()
    capabilities = capability_index(manifest)

    preview = [item for item in capabilities.values() if item["status"] == "preview"]
    assert preview
    for capability in preview:
        assert "action" not in capability
        assert "node" not in capability
        assert capability.get("future_interactions")


def test_only_declared_runtime_nodes_are_mutable_learning_nodes() -> None:
    manifest = load_manifest()
    capabilities = capability_index(manifest)
    allowed = set(manifest["contract"]["allowed_runtime_nodes"])

    runtime_capabilities = [
        item for item in capabilities.values() if item.get("action") in {"gold_loop", "repair"}
    ]
    assert runtime_capabilities
    assert {item["node"] for item in runtime_capabilities} <= allowed
    assert all(item["status"] in {"live", "limited"} for item in runtime_capabilities)

    topology_runtime_nodes = {
        node["id"] for node in manifest["topology"] if node["status"] == "runtime"
    }
    assert topology_runtime_nodes == allowed


def test_profile_and_baseline_framework_are_preserved() -> None:
    manifest = load_manifest()
    profile = manifest["profile"]
    capabilities = capability_index(manifest)

    assert set(profile) == {
        "learning_goal",
        "content_version",
        "learning_settings",
        "data_privacy",
    }
    assert capabilities["baseline_diagnostic"]["status"] == "preview"

    prd = PRD_PATH.read_text(encoding="utf-8")
    for token in [
        "# 11. 我的 Profile",
        "# 12. 基线测试与诊断入口",
        "LIVE / LIMITED / PREVIEW / LOCKED",
        "PREVIEW 内容完全由 Product Manifest 驱动",
    ]:
        assert token in prd, f"PRD V3 contract token missing: {token}"
