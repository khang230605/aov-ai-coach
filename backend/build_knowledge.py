import json
import os
from collections import defaultdict

def build_knowledge_base():
    print("🧠 ĐANG XÂY DỰNG TỪ ĐIỂN CHIẾN THUẬT CHO AI ĐỂ LÀM CHATBOT...")
    
    try:
        with open('data/all_matches_master.json', 'r', encoding='utf-8') as f:
            matches = json.load(f)
    except FileNotFoundError:
        print("❌ Không tìm thấy file dữ liệu.")
        return

    # Khởi tạo các bộ đếm
    hero_stats = defaultdict(lambda: {"picks": 0, "wins": 0, "bans": 0})
    synergy = defaultdict(lambda: defaultdict(lambda: {"matches": 0, "wins": 0}))
    counter = defaultdict(lambda: defaultdict(lambda: {"matches": 0, "wins": 0}))

    for match in matches:
        left = match['left_team']
        right = match['right_team']
        
        # Hàm nội bộ xử lý thống kê cho 1 đội
        def process_team(team, opp_team, is_win):
            picks = team['picks']
            opp_picks = opp_team['picks']
            bans = team['bans']
            
            # Cập nhật Ban/Pick chung
            for hero in bans:
                hero_stats[hero]["bans"] += 1
            for hero in picks:
                hero_stats[hero]["picks"] += 1
                if is_win:
                    hero_stats[hero]["wins"] += 1
                    
                # Cập nhật Phối hợp (Synergy) - Cùng đội
                for ally in picks:
                    if hero != ally:
                        synergy[hero][ally]["matches"] += 1
                        if is_win:
                            synergy[hero][ally]["wins"] += 1
                            
                # Cập nhật Khắc chế (Counter) - Khác đội
                for enemy in opp_picks:
                    counter[hero][enemy]["matches"] += 1
                    if is_win:
                        counter[hero][enemy]["wins"] += 1

        # Xử lý cho cả 2 đội
        process_team(left, right, left['is_winner'])
        process_team(right, left, right['is_winner'])

    # Lọc và tính tỷ lệ (Chỉ lấy những cặp có ít nhất 3 lần chạm trán để tránh dữ liệu rác)
    knowledge = {
        "meta_heroes": {},
        "best_synergies": {},
        "best_counters": {}
    }

    # 1. Tính Meta Heroes (Tỷ lệ pick/thắng cao)
    for hero, stat in hero_stats.items():
        if stat["picks"] >= 5: # Chỉ xét tướng pick trên 5 lần
            wr = round(stat["wins"] / stat["picks"] * 100, 2)
            knowledge["meta_heroes"][hero] = {"winrate": wr, "picks": stat["picks"]}

    # 2. Tính Synergy (Phối hợp)
    for hero, allies in synergy.items():
        knowledge["best_synergies"][hero] = {}
        for ally, stat in allies.items():
            if stat["matches"] >= 3:
                wr = round(stat["wins"] / stat["matches"] * 100, 2)
                knowledge["best_synergies"][hero][ally] = {"winrate": wr, "matches": stat["matches"]}

    # 3. Tính Counter (Khắc chế)
    for hero, enemies in counter.items():
        knowledge["best_counters"][hero] = {}
        for enemy, stat in enemies.items():
            if stat["matches"] >= 3:
                wr = round(stat["wins"] / stat["matches"] * 100, 2)
                # Nếu tỷ lệ thắng của Hero trước Enemy > 55% thì được coi là khắc chế
                if wr > 50: 
                    knowledge["best_counters"][hero][enemy] = {"winrate": wr, "matches": stat["matches"]}

    # Lưu ra file JSON
    os.makedirs('data', exist_ok=True)
    with open('data/knowledge_base.json', 'w', encoding='utf-8') as f:
        json.dump(knowledge, f, ensure_ascii=False, indent=4)
        
    print("✅ Đã tạo xong Knowledge Base!")
    print("👉 Hãy mở file data/knowledge_base.json để xem 'bí kíp' của AI.")

if __name__ == "__main__":
    build_knowledge_base()