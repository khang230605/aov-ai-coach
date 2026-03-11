import requests
from bs4 import BeautifulSoup
import json
import os
import re

def scrape_garena_heroes():
    url = "https://lienquan.garena.vn/hoc-vien/tuong-skin/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    # Bảng quy đổi ID class sang tên vai trò (Role)
    role_mapping = {
        "28": "Đấu sĩ",
        "31": "Đỡ đòn",
        "29": "Pháp sư",
        "32": "Sát thủ",
        "30": "Trợ thủ",
        "33": "Xạ thủ"
    }

    try:
        print("Đang tải dữ liệu từ Garena...")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Tìm tất cả các thẻ a chứa thông tin tướng dựa theo cấu trúc HTML bạn tìm được
        hero_elements = soup.find_all('a', class_='st-heroes__item')
        
        heroes_data = []
        for item in hero_elements:
            # Lấy tên tướng
            name_tag = item.find('h2', class_='st-heroes__item--name')
            hero_name = name_tag.text.strip() if name_tag else "Unknown"
            
            # Lấy keyword (ID)
            keyword = item.get('data-keyword', '').strip()
            
            # Lấy role (xử lý chuỗi như "[31][30]" thành mảng ["31", "30"])
            data_type_raw = item.get('data-type', '')
            role_ids = re.findall(r'\[(\d+)\]', data_type_raw.replace('][', '] ['))
            roles = [role_mapping.get(r_id, "Unknown") for r_id in role_ids]
            
            # Lấy link ảnh avatar
            img_container = item.find('div', class_='st-heroes__item--img')
            img_tag = img_container.find('img') if img_container else None
            avatar_url = img_tag['src'] if img_tag and 'src' in img_tag.attrs else ""
            
            heroes_data.append({
                "keyword": keyword,
                "name": hero_name,
                "roles": roles,
                "avatar": avatar_url
            })
            
        return heroes_data

    except Exception as e:
        print(f"Lỗi khi cào dữ liệu: {e}")
        return []

if __name__ == "__main__":
    heroes = scrape_garena_heroes()
    
    if heroes:
        os.makedirs("../data", exist_ok=True)
        with open('../data/heroes.json', 'w', encoding='utf-8') as f:
            json.dump(heroes, f, ensure_ascii=False, indent=4)
            
        print(f"Thành công cực kỳ! Đã cào và lưu trữ {len(heroes)} tướng.")
        print("Ví dụ dữ liệu con tướng đầu tiên:", heroes[0])
    else:
        print("Có lỗi xảy ra, không lấy được tướng nào.")