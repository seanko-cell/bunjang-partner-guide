"""
Bunjang API 자동 감지 & 업데이트 스크립트
─────────────────────────────────────────────
1. api.bgzt.guide에서 OpenAPI YAML 스펙 파싱
2. 변경사항 감지 (method / path / summary / parameters)
3. bunjang-partner-guide.html 자동 업데이트
4. build.py 실행 → GitHub 자동 배포
5. Slack 알림 발송

실행: python check_api.py
스케줄: setup_scheduler.bat 실행 시 매주 월요일 11:00 자동 등록
"""

import requests, json, os, re, subprocess, sys
from datetime import datetime

# ── 설정: 환경변수(GitHub Actions) 우선, 없으면 api_config.json 사용 ──
_cfg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "api_config.json")
_cfg = json.load(open(_cfg_path, encoding="utf-8")) if os.path.exists(_cfg_path) else {}
SLACK_WEBHOOK      = os.environ.get("SLACK_WEBHOOK")  or _cfg.get("SLACK_WEBHOOK", "")
SLACK_USER_ID      = os.environ.get("SLACK_USER_ID")  or _cfg.get("SLACK_USER_ID", "")
IN_GITHUB_ACTIONS  = os.environ.get("GITHUB_ACTIONS") == "true"
# ────────────────────────────────────────────────────────────────────

DIR          = os.path.dirname(os.path.abspath(__file__))
GUIDE_HTML   = os.path.join(DIR, "bunjang-partner-guide.html")
SNAPSHOT     = os.path.join(DIR, "api_snapshot.json")
HEADERS      = {"User-Agent": "Mozilla/5.0 (compatible; BunjangAPIChecker/1.0)",
                "Accept": "application/json, text/plain, */*"}


# ── YAML 파서 (pyyaml 없으면 경량 폴백) ─────────────────────────────
try:
    import yaml
    def parse_spec(text):
        return yaml.safe_load(text)
except ImportError:
    def parse_spec(text):
        """pyyaml 미설치 시 핵심 필드만 정규식으로 추출"""
        paths = re.findall(r'^  (/[^\s:]+):', text, re.MULTILINE)
        methods = re.findall(r'^\s{4}(get|post|put|delete|patch):', text, re.MULTILINE)
        summary = re.search(r'summary:\s*(.+)', text)
        return {
            "_fallback": True,
            "paths": {p: {m: {"summary": summary.group(1).strip() if summary else ""}}
                      for p, m in zip(paths[:1], methods[:1])}
        }


# ── API 링크 추출 ────────────────────────────────────────────────────
def extract_links():
    with open(GUIDE_HTML, "r", encoding="utf-8") as f:
        html = f.read()

    # Link 앞 셀의 API명과 URL을 함께 추출
    pattern = r'<td>([^<]{2,80})</td>\s*<td[^>]*>.*?href="(https://api\.bgzt\.guide/api-\d+)"'
    found = {}
    for name, url in re.findall(pattern, html, re.DOTALL):
        api_id = url.split("/")[-1]
        found[api_id] = {"name": name.strip(), "url": url}

    # 위 패턴에서 누락된 링크 보완
    for url in re.findall(r'https://api\.bgzt\.guide/api-\d+', html):
        api_id = url.split("/")[-1]
        if api_id not in found:
            found[api_id] = {"name": api_id, "url": url}

    return found


# ── API spec 파싱 ────────────────────────────────────────────────────
def fetch_spec(url):
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    spec = parse_spec(r.text)

    result = {"url": url, "raw_hash": _md5(r.text)}

    if not spec or "paths" not in spec:
        return result

    paths = spec.get("paths", {})
    if not paths:
        return result

    path = list(paths.keys())[0]
    methods = {k: v for k, v in paths[path].items()
               if k in ("get", "post", "put", "delete", "patch")}
    if not methods:
        return result

    method = list(methods.keys())[0]
    op = methods[method]

    params = op.get("parameters", [])
    param_names = sorted([p.get("name", "") for p in params if isinstance(p, dict)])

    result.update({
        "path":    path,
        "method":  method.upper(),
        "summary": op.get("summary", ""),
        "params":  param_names,
    })
    return result


def _md5(text):
    import hashlib
    return hashlib.md5(text.encode()).hexdigest()


# ── HTML 자동 업데이트 ───────────────────────────────────────────────
def update_html(api_id, old, new):
    """method / path / summary 변경 시 HTML 자동 수정"""
    with open(GUIDE_HTML, "r", encoding="utf-8") as f:
        html = f.read()

    url = new["url"]
    changed_fields = []

    # api_id 링크가 포함된 <tr> 블록 찾기
    tr_pattern = re.compile(
        r'(<tr>(?:(?!</tr>).)*?' + re.escape(url) + r'(?:(?!</tr>).)*?</tr>)',
        re.DOTALL
    )
    match = tr_pattern.search(html)
    if not match:
        return False, []

    original_tr = match.group(1)
    updated_tr = original_tr

    # ① method 변경
    if old.get("method") and new.get("method") and old["method"] != new["method"]:
        old_m = old["method"].lower()
        new_m = new["method"].lower()
        updated_tr = re.sub(
            rf'<span class="badge {old_m}">{old["method"]}</span>',
            f'<span class="badge {new_m}">{new["method"]}</span>',
            updated_tr
        )
        changed_fields.append(f"Method: `{old['method']}` → `{new['method']}`")

    # ② path 변경
    if old.get("path") and new.get("path") and old["path"] != new["path"]:
        updated_tr = updated_tr.replace(
            f'<code>{old["path"]}</code>',
            f'<code>{new["path"]}</code>'
        )
        changed_fields.append(f"Path: `{old['path']}` → `{new['path']}`")

    # ③ summary(API명) 변경
    if old.get("summary") and new.get("summary") and old["summary"] != new["summary"]:
        updated_tr = updated_tr.replace(old["summary"], new["summary"])
        changed_fields.append(f"Name: `{old['summary']}` → `{new['summary']}`")

    if updated_tr != original_tr:
        html = html.replace(original_tr, updated_tr)
        with open(GUIDE_HTML, "w", encoding="utf-8") as f:
            f.write(html)
        return True, changed_fields

    return False, []


# ── 배포 ─────────────────────────────────────────────────────────────
def deploy(commit_msg):
    steps = [
        ["python", "build.py"],
        ["git", "add", "."],
        ["git", "commit", "-m", commit_msg],
        ["git", "push", "-u", "origin", "main"],
    ]
    for cmd in steps:
        result = subprocess.run(cmd, cwd=DIR, capture_output=True, text=True)
        if result.returncode != 0 and "nothing to commit" not in result.stdout:
            print(f"  ⚠️  {' '.join(cmd)}: {result.stderr.strip()[:200]}")


# ── Slack 알림 ───────────────────────────────────────────────────────
def send_slack(blocks_text):
    if not SLACK_WEBHOOK:
        return
    try:
        requests.post(SLACK_WEBHOOK, json={"text": blocks_text}, timeout=5)
        print("  ✅ Slack 알림 발송 완료")
    except Exception as e:
        print(f"  ⚠️  Slack 발송 실패: {e}")


# ── 메인 ─────────────────────────────────────────────────────────────
def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"=== Bunjang API 자동 체크 ({now}) ===\n")

    links = extract_links()
    print(f"파트너 가이드에서 {len(links)}개 API 링크 발견\n")

    old_snap = json.load(open(SNAPSHOT, encoding="utf-8")) if os.path.exists(SNAPSHOT) else {}
    new_snap  = {}

    auto_updated  = []   # 자동 수정된 항목
    needs_review  = []   # 파라미터/응답 변경 (수동 검토 필요)
    new_apis      = []   # 신규 API
    removed_apis  = []   # 삭제된 API
    errors        = []

    for api_id, meta in links.items():
        name, url = meta["name"], meta["url"]
        try:
            spec = fetch_spec(url)
            new_snap[api_id] = {**meta, **spec}

            if api_id not in old_snap:
                new_apis.append(f"🆕 신규: *{name}* — `{spec.get('method','?')} {spec.get('path','?')}`")
                print(f"  [NEW]     {name}")
                continue

            old_spec = old_snap[api_id]

            # 해시 같으면 변경 없음
            if spec.get("raw_hash") == old_spec.get("raw_hash"):
                print(f"  [OK]      {name}")
                continue

            # method / path / summary 변경 → 자동 수정
            key_changed = (
                spec.get("method")  != old_spec.get("method") or
                spec.get("path")    != old_spec.get("path")   or
                spec.get("summary") != old_spec.get("summary")
            )
            param_changed = spec.get("params") != old_spec.get("params")

            if key_changed:
                ok, fields = update_html(api_id, old_spec, spec)
                if ok:
                    auto_updated.append(f"✏️  자동 수정: *{name}*\n   " + " / ".join(fields))
                    print(f"  [UPDATED] {name} — {', '.join(fields)}")
                else:
                    needs_review.append(f"⚠️  수동 확인 필요: *{name}* (HTML 패턴 불일치)\n   {url}")
                    print(f"  [REVIEW]  {name}")

            if param_changed:
                old_p = old_spec.get("params", [])
                new_p = spec.get("params", [])
                added   = [p for p in new_p if p not in old_p]
                removed = [p for p in old_p if p not in new_p]
                detail  = []
                if added:   detail.append(f"파라미터 추가: {added}")
                if removed: detail.append(f"파라미터 제거: {removed}")
                needs_review.append(f"⚠️  파라미터 변경: *{name}*\n   " + " / ".join(detail))
                print(f"  [PARAMS]  {name} — {detail}")

        except Exception as e:
            errors.append(f"❌ 오류: *{name}* ({e})")
            print(f"  [ERROR]   {name}: {e}")

    # 삭제된 API
    for api_id, old_meta in old_snap.items():
        if api_id not in new_snap:
            removed_apis.append(f"🗑️  삭제/이동됨: *{old_meta.get('name', api_id)}*")
            print(f"  [REMOVED] {old_meta.get('name', api_id)}")

    # 변경사항 있으면 배포 (로컬 실행 시만 — GitHub Actions는 workflow가 처리)
    all_changes = auto_updated + needs_review + new_apis + removed_apis + errors
    deployed = False
    if auto_updated and not IN_GITHUB_ACTIONS:
        commit_msg = f"auto: API spec update {now}"
        print(f"\n배포 중...")
        deploy(commit_msg)
        deployed = True
    elif auto_updated and IN_GITHUB_ACTIONS:
        deployed = True  # workflow의 Commit step이 처리

    json.dump(new_snap, open(SNAPSHOT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    # ── Slack 메시지 ──────────────────────────────────────────────────
    print(f"\n{'='*54}")
    mention = f"<@{SLACK_USER_ID}> " if SLACK_USER_ID else ""

    if not all_changes:
        msg = f"{mention}*[API 모니터링]* {now}\n✅ 변경사항 없음 — 전체 API 정상"
        print("✅ 변경사항 없음\n")
    else:
        sections = []
        if auto_updated:
            sections.append("*📝 자동 수정 완료*\n" + "\n".join(auto_updated))
        if needs_review:
            sections.append("*🔍 수동 검토 필요*\n" + "\n".join(needs_review))
        if new_apis:
            sections.append("*🆕 신규 API*\n" + "\n".join(new_apis))
        if removed_apis:
            sections.append("*🗑️ 삭제/이동*\n" + "\n".join(removed_apis))
        if errors:
            sections.append("*❌ 오류*\n" + "\n".join(errors))
        if deployed:
            sections.append(f"*🚀 배포 완료*\nhttps://seanko-cell.github.io/bunjang-partner-guide/")

        msg = f"{mention}*[API 모니터링]* {now}\n\n" + "\n\n".join(sections)
        print(msg)

    send_slack(msg)
    print(f"\n스냅샷 저장: api_snapshot.json\n")


if __name__ == "__main__":
    main()
