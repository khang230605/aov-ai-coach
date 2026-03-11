import json
import requests
import os
import time

def download_aov_images():
    save_dir = "../frontend/public/assets/heroes"
    os.makedirs(save_dir, exist_ok=True)

    # Thêm "giấy thông hành" User-Agent để giả dạng trình duyệt
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://lienquan.garena.vn/" # Thêm cái này để Garena tưởng bạn đang ở trên web của họ
    }

    try:
        with open('data/heroes.json', 'r', encoding='utf-8') as f:
            heroes = json.load(f)
    except FileNotFoundError:
        print("❌ Không tìm thấy heroes.json")
        return

    print(f"🚀 Bắt đầu tải {len(heroes)} ảnh tướng...")

    for hero in heroes:
        img_url = hero.get('avatar')
        if not img_url: continue

        file_name = f"{hero['keyword']}.jpg"
        file_path = os.path.join(save_dir, file_name)

        # Nếu ảnh đã tồn tại thì bỏ qua để tiết kiệm thời gian
        if os.path.exists(file_path):
            print(f"⏩ Đã có: {file_name}")
            continue

        try:
            # Thêm headers=headers vào đây
            response = requests.get(img_url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                print(f"✅ Đã tải: {file_name}")
            else:
                print(f"❌ Lỗi {response.status_code} tại {hero['name']}")
        except Exception as e:
            print(f"❌ Lỗi: {e}")
        
        # Nghỉ lâu hơn một chút (0.5s) để an toàn
        time.sleep(0.5)

if __name__ == "__main__":
    download_aov_images()