"""
빌드 스크립트:
1. 이미지 블러 + base64 내장 → 공유용 단일 HTML 생성
2. hub_completed 폴더 스캔 → index.html 자동 생성
실행: python build.py
"""

import os, base64, re, mimetypes, shutil, datetime
from PIL import Image, ImageFilter
import io

DIR = os.path.dirname(os.path.abspath(__file__))
HUB_DIR = os.path.join(DIR, "hub_completed")

# ─── 1. 파트너 가이드 빌드 ───────────────────────────────────────

IMAGES = {
    "order-status-flow.png":     0,
    "multi-product-listing.png": 0,
    "multi-product-cs.png":      0,
}

SOURCE_HTML = os.path.join(DIR, "bunjang-partner-guide.html")
OUTPUT_HTML = os.path.join(DIR, "bunjang-partner-guide-share.html")

def to_base64(filename, blur_radius):
    path = os.path.join(DIR, filename)
    if not os.path.exists(path):
        print(f"  [SKIP] 파일 없음: {filename}")
        return None
    img = Image.open(path)
    if blur_radius > 0:
        img = img.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    print(f"  [OK] {filename} → base64 변환 완료")
    return f"data:image/png;base64,{b64}"

print("=== [1/2] 파트너 가이드 빌드 ===\n")

if os.path.exists(SOURCE_HTML):
    with open(SOURCE_HTML, "r", encoding="utf-8") as f:
        html = f.read()
    for filename, blur in IMAGES.items():
        data_uri = to_base64(filename, blur)
        if data_uri:
            html = html.replace(f'src="{filename}"', f'src="{data_uri}"')
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\n  ✅ bunjang-partner-guide-share.html 생성 완료")

    # hub_completed에 자동 복사 (표시용 파일명으로 저장)
    os.makedirs(HUB_DIR, exist_ok=True)
    hub_copy = os.path.join(HUB_DIR, "글로벌_파트너_가이드.html")
    # 구 파일명 정리
    old_copy = os.path.join(HUB_DIR, "bunjang-partner-guide-share.html")
    if os.path.exists(old_copy):
        os.remove(old_copy)
    shutil.copy2(OUTPUT_HTML, hub_copy)
    print(f"  ✅ hub_completed에 자동 복사 완료 (글로벌_파트너_가이드.html)")
else:
    print("  [SKIP] bunjang-partner-guide.html 없음")

# ─── 2. hub_completed HTML 이미지 내장 처리 ─────────────────────

def embed_images_in_html(html_path):
    """HTML 파일 내의 로컬 이미지를 base64로 내장"""
    html_dir = os.path.dirname(html_path)
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    # src="..." 또는 src='...' 패턴에서 로컬 이미지 찾기
    pattern = r'src=["\'](?!data:)(?!http)([^"\']+\.(png|jpg|jpeg|gif|webp|svg))["\']'
    matches = re.findall(pattern, html, re.IGNORECASE)

    changed = False
    for img_rel, _ in matches:
        img_path = os.path.join(html_dir, img_rel)
        if not os.path.exists(img_path):
            print(f"    [SKIP] 이미지 없음: {img_rel}")
            continue
        mime, _ = mimetypes.guess_type(img_path)
        mime = mime or "image/png"
        with open(img_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        data_uri = f"data:{mime};base64,{b64}"
        html = html.replace(f'src="{img_rel}"', f'src="{data_uri}"')
        html = html.replace(f"src='{img_rel}'", f'src="{data_uri}"')
        print(f"    [OK] {img_rel} → base64 내장")
        changed = True

    if changed:
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)

print("\n=== [2/3] hub_completed 이미지 내장 처리 ===\n")
os.makedirs(HUB_DIR, exist_ok=True)
hub_files = [f for f in os.listdir(HUB_DIR) if f.endswith(".html")]
for fname in hub_files:
    print(f"  처리 중: {fname}")
    embed_images_in_html(os.path.join(HUB_DIR, fname))

# ─── 3. index.html 자동 생성 ────────────────────────────────────

print("\n=== [3/3] index.html 생성 ===\n")

os.makedirs(HUB_DIR, exist_ok=True)

# hub_completed 폴더의 HTML 파일 목록 수집
files = sorted([f for f in os.listdir(HUB_DIR) if f.endswith(".html")])
print(f"  hub_completed 폴더 파일 {len(files)}개 발견")

def make_label(filename):
    return filename.replace(".html", "").replace("-", " ").replace("_", " ")

FILE_ICON_SVG = """<svg width="16" height="18" viewBox="0 0 16 18" fill="none">
              <path d="M2 1h8l4 4v12H2V1z" stroke="#FF6B2C" stroke-width="1.5" fill="none" stroke-linejoin="round"/>
              <path d="M10 1v4h4" stroke="#FF6B2C" stroke-width="1.5" fill="none" stroke-linejoin="round"/>
              <path d="M5 9h6M5 12h4" stroke="#FF6B2C" stroke-width="1.5" stroke-linecap="round"/>
            </svg>"""

cards_html = ""
if not files:
    cards_html = '<div class="empty">hub_completed 폴더에 HTML 파일을 넣어주세요</div>'
else:
    for f in files:
        label = make_label(f)
        cards_html += f"""
      <div class="file-row">
        <div class="file-row-left">
          <div class="file-icon-wrap">{FILE_ICON_SVG}</div>
          <div>
            <div class="file-name">{label}</div>
            <div class="file-path">hub_completed/{f}</div>
          </div>
        </div>
        <a class="btn-open" href="hub_completed/{f}" target="_blank">열기</a>
      </div>"""

build_time = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

index_html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate"/>
  <meta http-equiv="Pragma" content="no-cache"/>
  <meta http-equiv="Expires" content="0"/>
  <title>Global BD Hub</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans KR', Roboto, sans-serif;
      background: #f7f8fa;
      min-height: 100vh;
      color: #1a1a1a;
    }}
    nav {{
      background: #fff;
      border-bottom: 1px solid #e5e8eb;
      padding: 0 40px;
      height: 60px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      position: sticky;
      top: 0;
      z-index: 100;
    }}
    .nav-left {{ display: flex; align-items: center; gap: 12px; }}
    .nav-logo {{ display: flex; align-items: center; gap: 8px; text-decoration: none; }}
    .nav-logo-bolt {{
      width: 32px; height: 32px; background: #FF6B2C; border-radius: 7px;
      display: flex; align-items: center; justify-content: center; flex-shrink: 0;
    }}
    .nav-brand {{ font-size: 16px; font-weight: 800; color: #1a1a1a; letter-spacing: -0.3px; }}
    .nav-divider {{ width: 1px; height: 18px; background: #e0e0e0; margin: 0 4px; }}
    .nav-sub {{ font-size: 13px; font-weight: 600; color: #555; }}
    .nav-badge {{
      font-size: 11px; color: #FF6B2C; background: #fff2ec;
      padding: 2px 8px; border-radius: 20px; font-weight: 600;
    }}
    .nav-user {{ font-size: 12px; color: #aaa; }}
    .container {{ max-width: 900px; margin: 0 auto; padding: 44px 24px; }}
    .page-title {{ font-size: 22px; font-weight: 700; color: #1a1a1a; margin-bottom: 6px; }}
    .page-desc {{ font-size: 13px; color: #aaa; margin-bottom: 24px; }}
    .file-list-card {{
      background: #fff;
      border: 1px solid #e5e8eb;
      border-radius: 12px;
      overflow: hidden;
    }}
    .list-header {{
      padding: 14px 24px;
      border-bottom: 1px solid #e5e8eb;
      display: flex;
      align-items: center;
      justify-content: space-between;
      background: #fafafa;
    }}
    .list-header-title {{ font-size: 12px; font-weight: 600; color: #888; letter-spacing: 0.3px; text-transform: uppercase; }}
    .list-count {{
      font-size: 12px; color: #fff; background: #FF6B2C;
      padding: 1px 9px; border-radius: 20px; font-weight: 600;
    }}
    .file-row {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 18px 24px;
      border-bottom: 1px solid #f2f2f2;
      transition: background 0.12s;
    }}
    .file-row:last-child {{ border-bottom: none; }}
    .file-row:hover {{ background: #fffaf8; }}
    .file-row-left {{ display: flex; align-items: center; gap: 16px; }}
    .file-icon-wrap {{
      width: 36px; height: 36px; background: #fff2ec; border-radius: 8px;
      display: flex; align-items: center; justify-content: center; flex-shrink: 0;
    }}
    .file-name {{ font-size: 14px; font-weight: 600; color: #1a1a1a; }}
    .file-path {{ font-size: 12px; color: #bbb; margin-top: 3px; }}
    .btn-open {{
      padding: 7px 18px; background: #FF6B2C; color: white;
      border-radius: 7px; font-size: 13px; font-weight: 600;
      text-decoration: none; transition: background 0.12s; white-space: nowrap;
    }}
    .btn-open:hover {{ background: #e85a1a; }}
    .empty {{ text-align: center; color: #ccc; font-size: 14px; padding: 56px 0; }}
    footer {{
      text-align: center; padding: 36px; font-size: 12px; color: #ccc; margin-top: 12px;
    }}
  </style>
</head>
<body>
<nav>
  <div class="nav-left">
    <div class="nav-logo">
      <div class="nav-logo-bolt">
        <svg width="16" height="20" viewBox="0 0 16 20" fill="none">
          <path d="M9.5 0.5L1 11.5H7.5L5.5 19.5L15 8.5H8.5L9.5 0.5Z" fill="white"/>
        </svg>
      </div>
      <span class="nav-brand">BUNJANG</span>
    </div>
    <div class="nav-divider"></div>
    <span class="nav-sub">Global BD Hub</span>
    <span class="nav-badge">Internal</span>
  </div>
  <span class="nav-user">Sean Ko · Global Business</span>
</nav>
<div class="container">
  <div class="page-title">파일 목록</div>
  <div class="page-desc">hub_completed 폴더의 파일 · deploy.bat 실행 시 자동 업데이트</div>
  <div class="file-list-card">
    <div class="list-header">
      <span class="list-header-title">Documents</span>
      <span class="list-count">{len(files)}</span>
    </div>
    {cards_html}
  </div>
</div>
<footer>© Bunjang Co., Ltd. · Global Business Development</footer>
</body>
</html>"""

index_path = os.path.join(DIR, "index.html")
with open(index_path, "w", encoding="utf-8") as f:
    f.write(index_html)

print(f"  ✅ index.html 생성 완료 ({len(files)}개 파일 등록)")
print("\n=== 빌드 완료 ===")
