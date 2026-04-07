"""
빌드 스크립트: 이미지 블러 + base64 내장 → 공유용 단일 HTML 생성
실행: python build.py

결과물: bunjang-partner-guide-share.html (이 파일 하나만 공유하면 됨)
"""

import os, base64, re
from PIL import Image, ImageFilter
import io

DIR = os.path.dirname(os.path.abspath(__file__))

IMAGES = {
    "order-status-flow.png":    1,   # 블러 강도 (약)
    "multi-product-listing.png": 6,  # 블러 강도 (강)
    "multi-product-cs.png":      6,  # 블러 강도 (강)
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

print("=== 번개장터 파트너 가이드 빌드 시작 ===\n")

with open(SOURCE_HTML, "r", encoding="utf-8") as f:
    html = f.read()

for filename, blur in IMAGES.items():
    data_uri = to_base64(filename, blur)
    if data_uri:
        html = html.replace(f'src="{filename}"', f'src="{data_uri}"')

with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
    f.write(html)

print(f"\n✅ 완료! 공유용 파일: bunjang-partner-guide-share.html")
print("   이 파일 하나만 공유하면 이미지 포함 정상 표시됩니다.")
