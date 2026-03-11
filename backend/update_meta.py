import requests
from bs4 import BeautifulSoup
import json

def fetch_meta_data():
    urls = {
        "GCS": "https://liquipedia.net/honorofkings/Garena_Challenger_Series/2026/Spring/Statistics",
        "AOG": "https://liquipedia.net/honorofkings/Arena_of_Glory/2026/Spring/Statistics",
        "RPL": "https://liquipedia.net/honorofkings/RoV_Pro_League/2026/Summer/Statistics"
    }
    
    headers = {"User-Agent": "Mozilla/5.0"}
    meta_stats = {}

    for league, url in urls.items():
        print(f"📡 Đang lấy dữ liệu từ {league}...")
        # Lưu ý: Thực tế bạn cần dùng scraper để parse đúng bảng Statistics của Liquipedia
        # Ở đây tôi mô phỏng logic tổng hợp dữ liệu
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            # Logic parse HTML table ở đây (Sử dụng soup.find('table', {'class': 'sortable'}))
            pass 

    # Giả sử sau khi parse, chúng ta có danh sách top meta
    # Đây là ví dụ về cấu trúc dữ liệu sau khi tổng hợp:
    meta_priority = {
        "Aya": {"ban_rate": 95.0, "pick_rate": 4.0, "win_rate": 52.0},
        "Elsu": {"ban_rate": 80.0, "pick_rate": 15.0, "win_rate": 55.0},
        "Zuka": {"ban_rate": 40.0, "pick_rate": 50.0, "win_rate": 60.0},
        "Yue": {"ban_rate": 60.0, "pick_rate": 30.0, "win_rate": 50.0}
    }
    
    with open('data/meta_priority.json', 'w', encoding='utf-8') as f:
        json.dump(meta_priority, f, ensure_ascii=False, indent=2)
    print("✅ Đã cập nhật file meta_priority.json!")

if __name__ == "__main__":
    fetch_meta_data()