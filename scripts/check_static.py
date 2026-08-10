from pathlib import Path

root = Path(__file__).resolve().parents[1] / "apps" / "web"
required = [root / "index.html", root / "app.js", root / "style.css"]
missing = [str(path) for path in required if not path.exists()]
assert not missing, f"missing static files: {missing}"
html = (root / "index.html").read_text(encoding="utf-8")
assert "/app.js" in html and "/style.css" in html
js = (root / "app.js").read_text(encoding="utf-8")
for token in ["ANSWER_SUBMITTED", "VERIFY_ANSWER", "WORD_ANSWER", "crypto.randomUUID", "CLOSED LOOP"]:
    assert token in js, f"missing frontend contract token: {token}"
print("STATIC_H5_OK")
