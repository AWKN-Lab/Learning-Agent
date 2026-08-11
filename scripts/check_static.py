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
assert "/app.js" in html and "/style.css" in html

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

manifest = (root / "product-manifest.json").read_text(encoding="utf-8")
for token in [
    '"mece_structure"',
    '"five_whys"',
    '"instruction_flow"',
    '"physical_restore"',
    '"error_diagnosis"',
    '"triple_patch"',
    '"logic_puzzle"',
    '"component_library"',
    '"learning_report"',
]:
    assert token in manifest, f"missing product capability: {token}"

print("STATIC_H5_OK")
