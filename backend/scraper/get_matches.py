import requests
from bs4 import BeautifulSoup
import json
import time
import os
import glob

# --- HÀM BÓC TÁCH HTML (Giữ nguyên logic cực chuẩn của bạn) ---
def parse_match_elements(soup):
    matches_data = []
    games_html = soup.find_all('div', class_='brkts-popup-body-game')
    bans_html = soup.find_all('tr', class_='brkts-popup-mapveto__ban-round')

    for i in range(len(games_html)):
        game = games_html[i]
        
        # Lấy tướng Pick
        left_picks_container = game.find('div', class_='brkts-popup-body-element-thumbs')
        left_picks = [a['title'] for a in left_picks_container.find_all('a')] if left_picks_container else []
        
        right_picks_container = game.find('div', class_='brkts-popup-body-element-thumbs-right')
        right_picks = [a['title'] for a in right_picks_container.find_all('a')] if right_picks_container else []

        # Lấy Kết quả
        winloss_icons = game.find_all('div', class_='brkts-popup-winloss-icon')
        left_won = False
        if winloss_icons:
            icon_tag = winloss_icons[0].find('i')
            if icon_tag and 'fa-check' in icon_tag.get('class', []):
                left_won = True

        # Lấy tướng Ban
        left_bans, right_bans = [], []
        if i < len(bans_html):
            ban_row = bans_html[i]
            ban_cols = ban_row.find_all('td', class_='brkts-popup-mapveto__ban-round-picks')
            if len(ban_cols) >= 2:
                left_bans = [a['title'] for a in ban_cols[0].find_all('a')]
                right_bans = [a['title'] for a in ban_cols[1].find_all('a')]

        # Format lại dữ liệu
        formatted_match = {
             "left_team": {
                 "is_winner": left_won,
                 "picks": left_picks,
                 "bans": left_bans
             },
             "right_team": {
                 "is_winner": not left_won,
                 "picks": right_picks,
                 "bans": right_bans
             }
        }
        
        # Chỉ lấy những ván đấu có dữ liệu hợp lệ (có pick tướng)
        if len(left_picks) > 0 and len(right_picks) > 0:
            matches_data.append(formatted_match)

    return matches_data

# --- HÀM DUYỆT CÁC GIẢI ĐẤU ---
def scrape_multiple_tournaments(urls):
    all_matches = []
    
    # Headers khai báo đàng hoàng để Liquipedia không nhầm là bot spam DDoS
    headers = {
        "User-Agent": "AOV-Draft-AI-Research/1.0 (Contact:khangnguyennhat64@gmail.com)",
        "Accept-Encoding": "gzip, deflate"
    }

    for url in urls:
        print(f"\n🌐 Đang cào dữ liệu từ: {url}")
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            matches = parse_match_elements(soup)
            all_matches.extend(matches)
            print(f"✅ Đã lấy được {len(matches)} ván đấu hợp lệ.")
            
        except requests.exceptions.HTTPError as errh:
            print(f"❌ Lỗi HTTP (Có thể bị block hoặc sai URL): {errh}")
        except Exception as e:
            print(f"❌ Lỗi hệ thống: {e}")
            
        # NGHỈ 3 GIÂY ĐỂ BẢO VỆ IP (BẮT BUỘC)
        print("⏳ Đang nghỉ 3 giây để tránh Rate Limit...")
        time.sleep(3)

    return all_matches

if __name__ == "__main__":
    print("🚀 BẮT ĐẦU QUÉT VÀ GOM DỮ LIỆU TỪ CÁC FILE HTML...")
    
    # Tìm tất cả các file có đuôi .html trong thư mục scraper
    html_files = glob.glob('scraper/*.html')
    
    if not html_files:
        print("⚠️ Không tìm thấy file HTML nào trong thư mục scraper.")
    else:
        all_matches = []
        
        for file_path in html_files:
            print(f"\n🔍 Đang xử lý file: {file_path}")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                    
                soup = BeautifulSoup(html_content, 'html.parser')
                matches = parse_match_elements(soup)
                all_matches.extend(matches)
                print(f"✅ Bóc tách được: {len(matches)} ván đấu.")
            except Exception as e:
                print(f"❌ Lỗi khi đọc file {file_path}: {e}")
                
        # Lưu ra một file Master duy nhất
        if all_matches:
            os.makedirs("data", exist_ok=True)
            output_file = 'data/all_matches_master.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_matches, f, ensure_ascii=False, indent=4)
                
            print(f"\n🎉 HOÀN TẤT XUẤT SẮC! Đã gom thành công TỔNG CỘNG {len(all_matches)} ván đấu.")
            print(f"📁 Dữ liệu tổng được lưu tại: {output_file}")
        else:
            print("\n⚠️ Không có ván đấu nào được bóc tách từ các file.")