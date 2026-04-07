"""
이미지 블러 처리 스크립트
같은 폴더에 아래 3개 이미지 저장 후 실행:
  - order-status-flow.png
  - multi-product-listing.png
  - multi-product-cs.png

실행 방법: python blur_images.py
"""

from PIL import Image, ImageFilter
import os

script_dir = os.path.dirname(os.path.abspath(__file__))

images = [
    "order-status-flow.png",
    "multi-product-listing.png",
    "multi-product-cs.png",
]

for filename in images:
    path = os.path.join(script_dir, filename)
    if not os.path.exists(path):
        print(f"[SKIP] 파일 없음: {filename}")
        continue

    img = Image.open(path)

    if filename == "order-status-flow.png":
        # 도식 이미지 - 블러 약하게
        blurred = img.filter(ImageFilter.GaussianBlur(radius=1))
    else:
        # 개인정보 포함 이미지 - 블러 강하게
        blurred = img.filter(ImageFilter.GaussianBlur(radius=6))

    blurred.save(path)
    print(f"[OK] 블러 처리 완료: {filename}")

print("\n완료! HTML 파일을 열어서 이미지 확인하세요.")
