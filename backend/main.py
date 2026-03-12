from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Hàm chuẩn hóa tên để so sánh chính xác
def norm(name):
    return re.sub(r'[^a-z0-9]', '', str(name).lower())

# Load dữ liệu
with open('data/knowledge_base.json', 'r', encoding='utf-8') as f:
    kb = json.load(f)
with open('data/heroes.json', 'r', encoding='utf-8') as f:
    heroes_info = json.load(f)

# Load thêm file meta (Có try-except đề phòng lỗi file)
try:
    with open('data/meta_priority.json', 'r', encoding='utf-8') as f:
        meta_db = json.load(f)
except FileNotFoundError:
    meta_db = {}

# THÊM DÒNG NÀY: Chuẩn hóa key của meta_db để tra cứu nhanh lúc tính điểm Counter/Synergy
norm_meta_db = {norm(k): v for k, v in meta_db.items()}

# Mapping chuẩn xác hơn từ Role sang Lane
ROLE_TO_LANE = {
    "Sát thủ": "Jung",
    "Pháp sư": "Mid",
    "Xạ thủ": "AD",
    "Trợ thủ": "SP",
    "Đỡ đòn": "SP",
    "Đấu sĩ": "Top"
}

# Tạo từ điển Hero để tra cứu nhanh O(1)
hero_db = {norm(h['name']): h for h in heroes_info}

def get_lanes(hero_name):
    n_name = norm(hero_name)
    if n_name in hero_db:
        return [ROLE_TO_LANE.get(r, "Flex") for r in hero_db[n_name]['roles']]
    return ["Flex"]

@app.get("/draft")
def draft_engine(
    your_team: str = "", 
    enemy_team: str = "", 
    bans: str = "",
    your_used: str = "",  # THÊM MỚI: Tướng team mình đã pick các game trước
    enemy_used: str = ""  # THÊM MỚI: Tướng team địch đã pick các game trước
):
    # 1. Chuẩn hóa đầu vào
    y_picks = [norm(x.strip()) for x in your_team.split(",") if x.strip()]
    e_picks = [norm(x.strip()) for x in enemy_team.split(",") if x.strip()]
    b_list = [norm(x.strip()) for x in bans.split(",") if x.strip()]
    
    # Chuẩn hóa danh sách tướng đã dùng ở các ván trước
    y_used_list = [norm(x.strip()) for x in your_used.split(",") if x.strip()]
    e_used_list = [norm(x.strip()) for x in enemy_used.split(",") if x.strip()]
    
    # Những tướng đang nằm trên bàn draft HIỆN TẠI (Pick & Ban của cả 2 team)
    current_draft_unavailable = set(y_picks + e_picks + b_list)
    
    # LUẬT GLOBAL BAN-PICK:
    # Tướng MÌNH không thể pick = Tướng đang trên bàn draft + Tướng mình đã dùng
    unavailable_for_you = current_draft_unavailable.union(set(y_used_list))
    
    # Tướng ĐỊCH không thể pick (và mình cũng không cần cấm) = Tướng đang trên bàn draft + Tướng địch đã dùng
    unavailable_for_enemy = current_draft_unavailable.union(set(e_used_list))

    # 2. Xác định các Lane đã có người
    your_occupied_lanes = []
    for p in y_picks:
        your_occupied_lanes.extend(get_lanes(p))
    
    enemy_occupied_lanes = []
    for p in e_picks:
        enemy_occupied_lanes.extend(get_lanes(p))

    def can_pick_for_lane(hero_name, occupied_list):
        h_lanes = get_lanes(hero_name)
        return any(lane not in occupied_list for lane in h_lanes)

    # --- LOGIC GIAI ĐOẠN ĐẦU (EARLY GAME DRAFT) ---
    if len(y_picks) + len(e_picks) < 2:
        early_picks = []
        early_bans = []
        
        for name, stat in meta_db.items():
            # Gợi ý PICK: Phải né tướng mình đã dùng
            if norm(name) not in unavailable_for_you:
                winrate = stat.get('win_rate', 0)
                meta_score = stat.get('meta_score', 0)
                early_picks.append({
                    "hero": name, 
                    "sort_key": meta_score, 
                    "score": winrate, 
                    "reason": "S-Tier Meta (Ưu tiên chọn)",
                    "type": "meta"
                })
                
            # Gợi ý BAN: Phải né tướng địch đã dùng
            if norm(name) not in unavailable_for_enemy:
                ban_rate = stat.get('ban_rate', 0)
                winrate = stat.get('win_rate', 0)
                early_bans.append({
                    "hero": name, 
                    "sort_key": ban_rate, 
                    "score": winrate,
                    "reason": f"Tướng cực nguy hiểm (Ban: {ban_rate}%)"
                })
        
        early_picks = sorted(early_picks, key=lambda x: x['sort_key'], reverse=True)
        early_bans = sorted(early_bans, key=lambda x: x['sort_key'], reverse=True)
        
        return {
            "pick_suggestions": early_picks[:8],
            "ban_suggestions": early_bans[:8]
        }

    # --- 3. GỢI Ý PICK (Mid/Late Game) ---
    pick_suggestions = []
    
    # Ưu tiên Counter
    for enemy in e_picks:
        target_enemy = next((h['name'] for h in heroes_info if norm(h['name']) == enemy), None)
        if not target_enemy: continue

        counters = kb["best_counters"].get(target_enemy, {})
        for h, stat in counters.items():
            h_norm = norm(h)
            # Áp dụng unavailable_for_you
            if h_norm not in unavailable_for_you and can_pick_for_lane(h, your_occupied_lanes):
                matchup_wr = stat.get("winrate", 50)
                meta_score = norm_meta_db.get(h_norm, {}).get('meta_score', 0)
                combined_score = (matchup_wr * 0.6) + (meta_score * 0.4)
                
                pick_suggestions.append({
                    "hero": h, 
                    "reason": f"Khắc chế {target_enemy}", 
                    "score": round(combined_score, 2),
                    "type": "counter"
                })

    # Ưu tiên Synergy
    for ally in y_picks:
        target_ally = next((h['name'] for h in heroes_info if norm(h['name']) == ally), None)
        if not target_ally: continue

        synergies = kb["best_synergies"].get(target_ally, {})
        for h, stat in synergies.items():
            h_norm = norm(h)
            # Áp dụng unavailable_for_you
            if h_norm not in unavailable_for_you and can_pick_for_lane(h, your_occupied_lanes):
                matchup_wr = stat.get("winrate", 50)
                meta_score = norm_meta_db.get(h_norm, {}).get('meta_score', 0)
                combined_score = (matchup_wr * 0.6) + (meta_score * 0.4)
                
                if not any(s['hero'] == h for s in pick_suggestions):
                    pick_suggestions.append({
                        "hero": h, 
                        "reason": f"Combo với {target_ally}", 
                        "score": round(combined_score, 2),
                        "type": "synergy"
                    })

    # FILLER LOGIC PICK
    if len(pick_suggestions) < 8:
        for name, stat in sorted(meta_db.items(), key=lambda x: x[1].get('meta_score', 0), reverse=True):
            # Áp dụng unavailable_for_you
            if norm(name) not in unavailable_for_you and can_pick_for_lane(name, your_occupied_lanes):
                if not any(s['hero'] == name for s in pick_suggestions):
                    pick_suggestions.append({
                        "hero": name, 
                        "reason": "Tướng Meta chuyên nghiệp", 
                        "score": stat.get('meta_score', 0), 
                        "type": "meta"
                    })
                    if len(pick_suggestions) >= 8: break

    # --- 4. GỢI Ý BAN ---
    ban_suggestions = []
    
    for enemy in e_picks:
        target_enemy = next((h['name'] for h in heroes_info if norm(h['name']) == enemy), None)
        e_synergies = kb["best_synergies"].get(target_enemy, {})
        for h, stat in e_synergies.items():
            h_norm = norm(h)
            # Áp dụng unavailable_for_enemy
            if h_norm not in unavailable_for_enemy and can_pick_for_lane(h, enemy_occupied_lanes):
                matchup_wr = stat.get("winrate", 50)
                meta_score = norm_meta_db.get(h_norm, {}).get('meta_score', 0)
                combined_score = (matchup_wr * 0.5) + (meta_score * 0.5)
                
                ban_suggestions.append({
                    "hero": h, 
                    "reason": f"Phá combo {target_enemy} - {h}", 
                    "score": round(combined_score, 2)
                })

    # FILLER LOGIC BAN
    if len(ban_suggestions) < 4:
        for name, stat in sorted(meta_db.items(), key=lambda x: x[1].get('ban_rate', 0), reverse=True):
            # Áp dụng unavailable_for_enemy
            if norm(name) not in unavailable_for_enemy and can_pick_for_lane(name, enemy_occupied_lanes):
                if not any(b['hero'] == name for b in ban_suggestions):
                    ban_suggestions.append({
                        "hero": name, 
                        "reason": f"Tướng cực nguy hiểm (Ban: {stat.get('ban_rate', 0)}%)", 
                        "score": stat.get('win_rate', 0)
                    })
                    if len(ban_suggestions) >= 4: break

    return {
        "pick_suggestions": sorted(pick_suggestions, key=lambda x: x['score'], reverse=True)[:8],
        "ban_suggestions": sorted(ban_suggestions, key=lambda x: x['score'], reverse=True)[:4]
    }

@app.get("/analyze")
def analyze_teams(your_team: str = "", enemy_team: str = ""):
    y_picks = [norm(x.strip()) for x in your_team.split(",") if x.strip()]
    e_picks = [norm(x.strip()) for x in enemy_team.split(",") if x.strip()]

    # Chỉ phân tích khi cả 2 bên đã chọn đủ 5 người
    if len(y_picks) < 5 or len(e_picks) < 5:
        return {"status": "error", "message": "Cần hoàn tất chọn 5 vs 5 để phân tích."}

    # --- HÀM ĐÁNH GIÁ ĐỘI HÌNH ---
    def evaluate_composition(team_picks):
        dive = poke = protect = 0
        total_meta_score = 0
        
        for h in team_picks:
            hero_data = next((item for item in heroes_info if norm(item['name']) == h), None)
            if hero_data:
                roles = hero_data.get('roles', [])
                # Chấm điểm lối chơi dựa trên Role
                if "Sát thủ" in roles or "Đấu sĩ" in roles: dive += 1.5
                if "Pháp sư" in roles or "Xạ thủ" in roles: poke += 1.5
                if "Trợ thủ" in roles or "Đỡ đòn" in roles: protect += 1.5
            
            # Cộng dồn sức mạnh Meta của cả đội
            total_meta_score += norm_meta_db.get(h, {}).get('meta_score', 50)
            
        # Xác định Lối chơi chủ đạo
        styles = {
            "Càn lướt (Dive)": dive,
            "Cấu rỉa (Poke)": poke,
            "Bảo kê (Protect)": protect
        }
        main_style = max(styles, key=styles.get)
        
        return main_style, total_meta_score

    # Phân tích 2 team
    y_style, y_meta = evaluate_composition(y_picks)
    e_style, e_meta = evaluate_composition(e_picks)

    # --- TÍNH TOÁN TỈ LỆ THẮNG (WIN PROBABILITY) ---
    # 1. Base winrate là 50%
    y_win_prob = 50.0 
    
    # 2. Cộng trừ dựa trên chênh lệch chất tướng (Meta Score)
    # Giả sử chênh lệch 50 điểm meta toàn đội -> Lệch 5% Winrate
    meta_diff = (y_meta - e_meta) * 0.1 
    y_win_prob += meta_diff

    # 3. Cộng trừ dựa trên Khắc chế Đội hình (Quy luật Kéo-Búa-Bao)
    matchup_bonus = 6.0 # Lợi thế khi khắc chế lối chơi là 6%
    if y_style == "Càn lướt (Dive)" and e_style == "Cấu rỉa (Poke)": y_win_prob += matchup_bonus
    elif y_style == "Cấu rỉa (Poke)" and e_style == "Bảo kê (Protect)": y_win_prob += matchup_bonus
    elif y_style == "Bảo kê (Protect)" and e_style == "Càn lướt (Dive)": y_win_prob += matchup_bonus
    
    elif e_style == "Càn lướt (Dive)" and y_style == "Cấu rỉa (Poke)": y_win_prob -= matchup_bonus
    elif e_style == "Cấu rỉa (Poke)" and y_style == "Bảo kê (Protect)": y_win_prob -= matchup_bonus
    elif e_style == "Bảo kê (Protect)" and y_style == "Càn lướt (Dive)": y_win_prob -= matchup_bonus

    # Khống chế winrate trong khoảng thực tế (20% - 80%)
    y_win_prob = max(20.0, min(80.0, y_win_prob))
    e_win_prob = 100.0 - y_win_prob

    # --- TẠO LỜI KHUYÊN (WIN CONDITION) ---
    advices = {
        "Càn lướt (Dive)": "Ép giao tranh sớm, bắt lẻ chủ lực địch. Tránh để trận đấu kéo quá late.",
        "Cấu rỉa (Poke)": "Giữ khoảng cách, cấu máu trước rồng/tà thần. Tuyệt đối không đứng lỗi vị trí.",
        "Bảo kê (Protect)": "Đi chung cùng nhau, nhường tài nguyên cho chủ lực. Chơi ôm trụ chờ late game."
    }
    
    matchup_advice = f"Đội bạn mạnh về {y_style}, trong khi địch là {e_style}. "
    if y_win_prob > 55:
        matchup_advice += "Đội hình bạn đang OUT-DRAFT đối thủ! "
    elif y_win_prob < 45:
        matchup_advice += "Đội hình địch đang có lợi thế chất tướng. "
    else:
        matchup_advice += "Kèo đấu cân bằng kỹ năng. "

    return {
        "status": "success",
        "analysis": {
            "your_team": {
                "playstyle": y_style,
                "win_probability": round(y_win_prob, 1),
                "win_condition": advices[y_style]
            },
            "enemy_team": {
                "playstyle": e_style,
                "win_probability": round(e_win_prob, 1),
                "win_condition": advices[e_style]
            },
            "coach_summary": matchup_advice + advices[y_style]
        }
    }