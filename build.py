"""
빌드 스크립트:
1. 이미지 블러 + base64 내장 → 공유용 단일 HTML 생성
2. hub_completed 폴더 스캔 → index.html 자동 생성
실행: python build.py
"""

import os, base64, re, mimetypes
from PIL import Image, ImageFilter
import io

DIR = os.path.dirname(os.path.abspath(__file__))
HUB_DIR = os.path.join(DIR, "hub_completed")

# ─── 1. 파트너 가이드 빌드 ───────────────────────────────────────

IMAGES = {
    "order-status-flow.png":     1,
    "multi-product-listing.png": 6,
    "multi-product-cs.png":      6,
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
    cards_html = '<p class="empty">hub_completed 폴더에 HTML 파일을 넣어주세요</p>'
else:
    for f in files:
        label = make_label(f)
        cards_html += f"""
      <div class="file-card">
        <div class="file-left">
          <div class="file-icon">📄</div>
          <div class="file-info">
            <div class="file-name">{label}</div>
            <div class="file-meta">hub_completed/{f}</div>
          </div>
        </div>
        <div class="file-actions">
          <a class="btn-open" href="hub_completed/{f}" target="_blank">열기</a>
        </div>
      </div>"""

index_html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Sean's HTML Hub</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: #f4f4f4;
      min-height: 100vh;
    }}
    header {{
      background: #FF6B2C;
      color: white;
      padding: 28px 40px;
    }}
    header h1 {{ font-size: 22px; font-weight: 700; }}
    header p {{ font-size: 13px; margin-top: 4px; opacity: 0.85; }}
    .container {{ max-width: 860px; margin: 0 auto; padding: 32px 24px; }}
    .section-title {{
      font-size: 13px; font-weight: 600; color: #aaa;
      text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 12px;
    }}
    .file-list {{ display: flex; flex-direction: column; gap: 12px; }}
    .file-card {{
      background: white; border-radius: 10px; padding: 16px 20px;
      display: flex; align-items: center; justify-content: space-between;
      box-shadow: 0 1px 4px rgba(0,0,0,0.07); transition: box-shadow 0.2s;
    }}
    .file-card:hover {{ box-shadow: 0 3px 10px rgba(0,0,0,0.12); }}
    .file-left {{ display: flex; align-items: center; gap: 14px; flex: 1; min-width: 0; }}
    .file-icon {{
      width: 40px; height: 40px; background: #fff2ec; border-radius: 8px;
      display: flex; align-items: center; justify-content: center; font-size: 20px; flex-shrink: 0;
    }}
    .file-name {{ font-weight: 600; font-size: 15px; color: #1a1a1a; }}
    .file-meta {{ font-size: 12px; color: #aaa; margin-top: 2px; }}
    .file-actions {{ display: flex; gap: 8px; flex-shrink: 0; margin-left: 16px; }}
    .btn-open {{
      padding: 7px 18px; background: #FF6B2C; color: white; border: none;
      border-radius: 6px; font-size: 13px; font-weight: 600; cursor: pointer;
      text-decoration: none; transition: background 0.2s;
    }}
    .btn-open:hover {{ background: #e85a1a; }}
    .empty {{ text-align: center; color: #ccc; font-size: 14px; padding: 20px 0; }}
    footer {{
      text-align: center; padding: 24px; font-size: 12px; color: #aaa;
      border-top: 1px solid #eee; margin-top: 40px;
    }}
  </style>
</head>
<body>
<header>
  <h1>📁 Sean's HTML Hub</h1>
  <p>hub_completed 폴더의 파일 목록 · deploy.bat 실행 시 자동 업데이트</p>
</header>
<div class="container">
  <div class="section-title">파일 목록 ({len(files)}개)</div>
  <div class="file-list">
    {cards_html}
  </div>
</div>
<footer>© Bunjang Co., Ltd.</footer>
</body>
</html>"""

index_path = os.path.join(DIR, "index.html")
with open(index_path, "w", encoding="utf-8") as f:
    f.write(index_html)

print(f"  ✅ index.html 생성 완료 ({len(files)}개 파일 등록)")
print("\n=== 빌드 완료 ===")
