import json
import pandas as pd
import re
import os

# Hàm chuẩn hóa tên: Viết thường toàn bộ và xóa sạch các dấu câu, khoảng trắng
def normalize_name(name):
    return re.sub(r'[^a-z0-9]', '', str(name).lower())

def create_ml_dataset():
    # 1. Tải từ điển Tướng
    try:
        with open('data/heroes.json', 'r', encoding='utf-8') as f:
            heroes = json.load(f)
    except FileNotFoundError:
        print("❌ Lỗi: Không tìm thấy file data/heroes.json")
        return

    # Tạo bộ từ điển mapping: Tên chuẩn hóa -> ID (vị trí cột)
    hero_to_id = {}
    for idx, hero in enumerate(heroes):
        # Lưu cả tên (name) và định danh (keyword) để tăng tỷ lệ khớp
        hero_to_id[normalize_name(hero['name'])] = idx
        hero_to_id[normalize_name(hero['keyword'])] = idx

    # Bổ sung thủ công một số tướng có tên quốc tế khác tên Garena Việt Nam
    # (Dựa trên file HTML bạn gửi lúc trước)
    custom_mapping = {
        'doria': 'dolia',
        'kuangtie': 'biron',
        'ailin': 'erin',
        'ybneth': 'ybneth', # Đề phòng dấu nháy đơn
        'jinnar': 'jinna', 'riktor': 'richter', 'zanis': 'trieuvan', "wirosableng" : "wiro", "sikongzhen" : "boltbaron"
    }
    for intl_name, vn_name in custom_mapping.items():
        if vn_name in hero_to_id:
            hero_to_id[intl_name] = hero_to_id[vn_name]

    num_heroes = len(heroes)

    # 2. Tải dữ liệu các ván đấu
    try:
        with open('data/all_matches_master.json', 'r', encoding='utf-8') as f:
            matches = json.load(f)
    except FileNotFoundError:
        print("❌ Lỗi: Không tìm thấy file data/all_matches_master.json")
        return

    dataset = []
    unmatched_heroes = set()

    print("⚙️ Đang mã hóa dữ liệu (One-Hot Encoding)...")
    
    # 3. Quá trình mã hóa
    for match in matches:
        left_team = match['left_team']
        right_team = match['right_team']

        # Khởi tạo ma trận toàn số 0
        left_vector = [0] * num_heroes
        right_vector = [0] * num_heroes

        # Mã hóa Tướng Chọn Đội Trái
        for hero_name in left_team['picks']:
            norm_name = normalize_name(hero_name)
            if norm_name in hero_to_id:
                left_vector[hero_to_id[norm_name]] = 1
            else:
                unmatched_heroes.add(hero_name)

        # Mã hóa Tướng Chọn Đội Phải
        for hero_name in right_team['picks']:
            norm_name = normalize_name(hero_name)
            if norm_name in hero_to_id:
                right_vector[hero_to_id[norm_name]] = 1
            else:
                unmatched_heroes.add(hero_name)

        # Cột Kết quả: 1 nếu Trái thắng, 0 nếu Trái thua
        label = 1 if left_team['is_winner'] else 0
        
        # Gộp lại thành 1 dòng dữ liệu
        row = left_vector + right_vector + [label]
        dataset.append(row)

    # Cảnh báo nếu có tướng nào Liquipedia có mà Garena chưa cập nhật
    if unmatched_heroes:
        print("\n⚠️ CẢNH BÁO: Các tướng sau từ Liquipedia không khớp được với dữ liệu Garena:")
        print(", ".join(unmatched_heroes))
        print("-> Cột của các tướng này sẽ bị bỏ qua (để = 0).\n")

    # 4. Lưu thành file CSV cho AI
    left_cols = [f"Left_{hero['keyword']}" for hero in heroes]
    right_cols = [f"Right_{hero['keyword']}" for hero in heroes]
    columns = left_cols + right_cols + ["Left_Win"]

    df = pd.DataFrame(dataset, columns=columns)
    output_path = 'data/ml_dataset.csv'
    df.to_csv(output_path, index=False, encoding='utf-8')
    
    print(f"✅ XONG! Đã tạo file CSV thành công.")
    print(f"📊 Kích thước ma trận: {df.shape[0]} ván đấu x {df.shape[1]} đặc trưng (cột).")
    print(f"📁 Đường dẫn: {output_path}")

if __name__ == "__main__":
    create_ml_dataset()