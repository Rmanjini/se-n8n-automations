"""Strip secrets/PII from n8n workflow exports. Usage: python3 sanitize.py <src_dir> <out_dir>"""
import json, re, sys, pathlib

DROP_TOP = {"pinData", "id", "versionId", "meta", "staticData", "tags", "shared", "triggerCount"}
SENSITIVE_HEADER = re.compile(r"key|token|auth|secret|password|cookie|signature", re.I)
SUBS = [
    (re.compile(r"Bearer\s+(?!\{\{)[A-Za-z0-9\-._~+/=]{10,}"), "Bearer YOUR_TOKEN"),
    (re.compile(r"eyJ[\w-]{10,}\.[\w-]{10,}\.[\w-]+"), "YOUR_JWT"),
    (re.compile(r"\b(sk|pk|rk)-[A-Za-z0-9_-]{16,}"), "YOUR_API_KEY"),
    (re.compile(r"\b(AIza[0-9A-Za-z_-]{30,}|gh[pousr]_[A-Za-z0-9]{30,}|xox[abprs]-[A-Za-z0-9-]{10,})"), "YOUR_API_KEY"),
    (re.compile(r"\b\d{8,10}:[A-Za-z0-9_-]{35}\b"), "YOUR_BOT_TOKEN"),
    # kylas-style key "uuid:tenant" and any bare uuid (webhook ids, bothook ids, etc.)
    (re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}(:\d+)?", re.I), "00000000-0000-0000-0000-000000000000"),
    (re.compile(r"script\.google\.com/macros/s/[A-Za-z0-9_-]+"), "script.google.com/macros/s/YOUR_SCRIPT_ID"),
    (re.compile(r"/spreadsheets/d/[A-Za-z0-9_-]+"), "/spreadsheets/d/YOUR_SHEET_ID"),
    (re.compile(r"https?://[\w.-]*zoom\.us/\S*"), "https://zoom.us/j/YOUR_MEETING"),
    (re.compile(r"([?&](?:api_?key|key|token|access_token|secret|pwd|password|sig)=)[^&\s\"']+", re.I), r"\1REDACTED"),
    (re.compile(r"https?://n8n\.[\w.-]+"), "https://your-n8n-host"),
    (re.compile(r"https?://[\w.-]*(hstgr\.cloud|ngrok[\w.-]*|edgeone\.app|app\.n8n\.cloud)\b", re.I), "https://your-n8n-host"),
    (re.compile(r"\b[0-9a-f]{24}\b"), "000000000000000000000000"),  # mongo-style object ids
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "user@example.com"),
    (re.compile(r"(?<![\w.])(\+?91[\s-]?)?[6-9]\d{9}(?!\d)"), "+910000000000"),
    # quoted string assigned to secret-ish identifiers in code
    (re.compile(r"""((?:api[_-]?key|apikey|token|secret|password|passwd|authorization|sid)['"]?\s*[:=]\s*['"])(?!\{\{|YOUR_|\$env)[^'"]{6,}(['"])""", re.I), r"\1YOUR_SECRET\2"),
]
SHEET_ID = re.compile(r"^=?[A-Za-z0-9_-]{30,60}$")

def scrub(s):
    for rx, rep in SUBS:
        s = rx.sub(rep, s)
    return s

def walk(x, key=""):
    if isinstance(x, dict):
        # header/query/body params: {"name": "api-key", "value": "..."}
        if isinstance(x.get("name"), str) and "value" in x and SENSITIVE_HEADER.search(x["name"]) \
                and isinstance(x["value"], str) and "$env" not in x["value"]:
            x = {**x, "value": "YOUR_" + re.sub(r"\W", "_", x["name"]).upper()}
        # google sheets resource locators
        if x.get("__rl") and isinstance(x.get("value"), str) and SHEET_ID.match(x["value"]):
            x = {**x, "value": "YOUR_SHEET_ID"}
        x = {k: walk(v, k) for k, v in x.items() if k not in ("cachedResultUrl",)}
        if "cachedResultName" in x: x["cachedResultName"] = "Sheet"
        return x
    if isinstance(x, list):
        return [walk(i, key) for i in x]
    if isinstance(x, str):
        return scrub(x)
    return x

def clean(wf):
    wf = {k: v for k, v in wf.items() if k not in DROP_TOP}
    wf["active"] = False
    for n in wf["nodes"]:
        n.pop("webhookId", None)
        for c in n.get("credentials", {}).values():
            c["id"] = "REPLACE_WITH_YOUR_CREDENTIAL"
        n["parameters"] = walk(n.get("parameters", {}))
        if "notes" in n: n["notes"] = scrub(n["notes"])
    return wf

def slug(name):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", re.sub(r"\(\d+\)", "", name.lower()))).strip("-")

if __name__ == "__main__":
    assert scrub("api-key: '12345678-aaaa-bbbb-cccc-1234567890ab:999'") == "api-key: 'YOUR_SECRET'"
    assert scrub("call 9876543210 or a@b.com") == "call +910000000000 or user@example.com"
    src, out = map(pathlib.Path, sys.argv[1:3])
    for f in sorted(src.glob("*.json")):
        wf = clean(json.loads(f.read_text()))
        (out / f"{slug(f.stem)}.json").write_text(json.dumps(wf, indent=2, ensure_ascii=False) + "\n")
        print(f.name, "->", slug(f.stem) + ".json")
