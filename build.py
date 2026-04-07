"""
빌드 스크립트:
1. 이미지 블러 + base64 내장 → 공유용 단일 HTML 생성
2. hub_completed 폴더 스캔 → index.html 자동 생성
실행: python build.py
"""

import os, base64, re, mimetypes, shutil
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

    # hub_completed에 자동 복사
    os.makedirs(HUB_DIR, exist_ok=True)
    hub_copy = os.path.join(HUB_DIR, "bunjang-partner-guide-share.html")
    shutil.copy2(OUTPUT_HTML, hub_copy)
    print(f"  ✅ hub_completed에 자동 복사 완료")
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

cards_html = ""
if not files:
    cards_html = '<div class="empty">hub_completed 폴더에 HTML 파일을 넣어주세요</div>'
else:
    for f in files:
        label = make_label(f)
        cards_html += f"""
      <div class="file-row">
        <div class="file-row-left">
          <div class="file-dot"></div>
          <div>
            <div class="file-name">{label}</div>
            <div class="file-path">hub_completed/{f}</div>
          </div>
        </div>
        <a class="btn-open" href="hub_completed/{f}" target="_blank">열기</a>
      </div>"""

index_html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
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
      height: 56px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      position: sticky;
      top: 0;
      z-index: 100;
    }}
    .nav-left {{ display: flex; align-items: center; gap: 10px; }}
    .nav-logo-icon {{
      width: 28px; height: 28px; background: #FF6B2C; border-radius: 6px;
      display: flex; align-items: center; justify-content: center;
      color: white; font-weight: 800; font-size: 13px; flex-shrink: 0;
    }}
    .nav-title {{ font-size: 15px; font-weight: 700; color: #1a1a1a; }}
    .nav-badge {{
      font-size: 11px; color: #888; background: #f0f0f0;
      padding: 2px 8px; border-radius: 20px;
    }}
    .nav-user {{ font-size: 12px; color: #aaa; }}
    .container {{ max-width: 900px; margin: 0 auto; padding: 40px 24px; }}
    .page-title {{ font-size: 20px; font-weight: 700; color: #1a1a1a; margin-bottom: 20px; }}
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
    }}
    .list-header-title {{ font-size: 13px; font-weight: 600; color: #555; }}
    .list-count {{ font-size: 12px; color: #aaa; }}
    .file-row {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 18px 24px;
      border-bottom: 1px solid #f2f2f2;
      transition: background 0.15s;
    }}
    .file-row:last-child {{ border-bottom: none; }}
    .file-row:hover {{ background: #fafafa; }}
    .file-row-left {{ display: flex; align-items: center; gap: 14px; }}
    .file-dot {{
      width: 7px; height: 7px; background: #FF6B2C;
      border-radius: 50%; flex-shrink: 0;
    }}
    .file-name {{ font-size: 14px; font-weight: 600; color: #1a1a1a; }}
    .file-path {{ font-size: 12px; color: #aaa; margin-top: 3px; }}
    .btn-open {{
      padding: 6px 16px; background: #FF6B2C; color: white;
      border-radius: 6px; font-size: 13px; font-weight: 600;
      text-decoration: none; transition: background 0.15s; white-space: nowrap;
    }}
    .btn-open:hover {{ background: #e85a1a; }}
    .empty {{ text-align: center; color: #ccc; font-size: 14px; padding: 48px 0; }}
    footer {{
      text-align: center; padding: 32px; font-size: 12px; color: #bbb; margin-top: 16px;
    }}
  </style>
</head>
<body>
<nav>
  <div class="nav-left">
    <div class="nav-logo-icon">B</div>
    <span class="nav-title">Global BD Hub</span>
    <span class="nav-badge">Internal</span>
  </div>
  <span class="nav-user">Sean Ko · Bunjang Global</span>
</nav>
<div class="container">
  <div class="page-title">파일 목록</div>
  <div class="file-list-card">
    <div class="list-header">
      <span class="list-header-title">hub_completed</span>
      <span class="list-count">{len(files)}개 파일</span>
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
