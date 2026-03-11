import os
import json
from bs4 import BeautifulSoup

def parse_liquipedia_html():
    files = ['data/aog_heroes.html', 'data/gcs_heroes.html', 'data/rpl_heroes.html']
    aggregated_data = {}
    total_picks_all_tournaments = 0
    
    for file in files:
        if not os.path.exists(file):
            print(f"⚠️ Không tìm thấy {file}, bỏ qua...")
            continue
            
        with open(file, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'lxml')
            
        # Thường bảng thống kê của Liquipedia có class 'sortable'
        tables = soup.find_all('table', class_='sortable')
        if not tables: continue
            
        table = tables[0] 
        rows = table.find('tbody').find_all('tr') if table.find('tbody') else table.find_all('tr')
        
        for row in rows:
            cols = row.find_all(['td', 'th'])
            if len(cols) < 7: continue # Bỏ qua header
                
            # Cột 1 hoặc 2 thường chứa tên tướng (trong thẻ <a>)
            a_tag = cols[0].find('a')
            if not a_tag and len(cols) > 1: a_tag = cols[1].find('a')
            if not a_tag: continue
            
            hero_name = a_tag.get('title', '').strip()
            if not hero_name: continue
            
            # Hàm lấy số từ text (Ví dụ "152" -> 152, "-" -> 0)
            def get_num(td):
                txt = td.text.strip().replace('%', '')
                return int(txt) if txt.isdigit() else 0
            
            # Cấu trúc cột Liquipedia: [0:Icon, 1:Tên, 2:Tổng P+B, 3:Pick, 4:Ban, 5:Win, 6:Loss, 7:Win%]
            # Chú ý: Có thể lệch 1 cột tùy trang, script này giả định Pick ở cột 3, Ban ở cột 4, Win ở cột 5
            try:
                picks = get_num(cols[2])
                bans = get_num(cols[3])
                wins = get_num(cols[4])
            except IndexError:
                continue
            
            if hero_name not in aggregated_data:
                aggregated_data[hero_name] = {'picks': 0, 'bans': 0, 'wins': 0}
                
            aggregated_data[hero_name]['picks'] += picks
            aggregated_data[hero_name]['bans'] += bans
            aggregated_data[hero_name]['wins'] += wins
            
            total_picks_all_tournaments += picks

    # Tính toán Rate và Meta Score
    total_matches = total_picks_all_tournaments / 10 if total_picks_all_tournaments > 0 else 1
    
    meta_priority = {}
    for hero, stats in aggregated_data.items():
        pick_rate = (stats['picks'] / total_matches) * 100
        ban_rate = (stats['bans'] / total_matches) * 100
        win_rate = (stats['wins'] / stats['picks']) * 100 if stats['picks'] > 0 else 0
        
        # Áp dụng công thức
        score = (ban_rate * 1.5) + (pick_rate * 1.0) + (win_rate * 0.5)
        
        meta_priority[hero] = {
            'pick_rate': round(pick_rate, 2),
            'ban_rate': round(ban_rate, 2),
            'win_rate': round(win_rate, 2),
            'meta_score': round(score, 2)
        }
        
    with open('data/meta_priority.json', 'w', encoding='utf-8') as f:
        json.dump(meta_priority, f, ensure_ascii=False, indent=2)
        
    print(f"✅ Đã phân tích {len(meta_priority)} tướng và lưu vào data/meta_priority.json")

if __name__ == "__main__":
    parse_liquipedia_html()