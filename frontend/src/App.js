import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { DRAFT_STEPS } from './constants';
import './App.css';
import heroesData from './heroes.json';

// Khởi tạo đối tượng Audio sẵn để không bị load lại nhiều lần
const pickSound = new Audio('/assets/sounds/pick.mp3');
pickSound.volume = 0.7; // Chỉnh âm lượng (từ 0.0 đến 1.0)

function App() {
  const [userSide, setUserSide] = useState(null);
  const [currentStepIdx, setCurrentStepIdx] = useState(0);
  const [draftData, setDraftData] = useState({
    bluePicks: [], redPicks: [], blueBans: [], redBans: []
  });
  const [suggestions, setSuggestions] = useState({ pick_suggestions: [], ban_suggestions: [] });

    const [analysisResult, setAnalysisResult] = useState(null);

  // Hàm chuẩn hóa chuỗi (xóa khoảng trắng, dấu phẩy, nháy đơn, viết thường)
  const normalizeName = (str) => {
    if (!str) return '';
    return str.toLowerCase().replace(/[^a-z0-9]/g, '');
  };

  // Hàm lấy ảnh thông minh đã được nâng cấp
  const getHeroAvatar = (name) => {
    if (!name) return null;
    
    // Tìm tướng bằng cách so sánh 2 tên đã chuẩn hóa
    const hero = heroesData.find(h => normalizeName(h.name) === normalizeName(name));
    
    // Nếu tìm thấy thì lấy keyword, không thì trả về default
    const keyword = hero ? hero.keyword.toLowerCase() : 'default';
    return `/assets/heroes/${keyword}.jpg`;
  };

  // 2. Kiểm tra xem tướng đã được chọn/cấm chưa (Tránh trùng lặp)
  const isHeroUnavailable = (heroName) => {
    const { bluePicks, redPicks, blueBans, redBans } = draftData;
    const allSelected = [...bluePicks, ...redPicks, ...blueBans, ...redBans];
    return allSelected.includes(heroName);
  };

    // 1. Thêm state mới ở đầu function App
    const [searchTerm, setSearchTerm] = useState("");

    // 2. Logic lọc tướng (đặt sau đoạn load heroesData)
    const filteredHeroes = heroesData.filter(hero => 
    hero.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    hero.keyword.toLowerCase().includes(searchTerm.toLowerCase())
    );
  useEffect(() => {
    const currentStep = DRAFT_STEPS[currentStepIdx];
    if (userSide && currentStep && currentStep.side === userSide) {
      const fetchAi = async () => {
        try {
          const res = await axios.get(`http://localhost:8000/draft`, {
            params: { 
              your_team: (userSide === 'Blue' ? draftData.bluePicks : draftData.redPicks).join(','), 
              enemy_team: (userSide === 'Blue' ? draftData.redPicks : draftData.bluePicks).join(','), 
              bans: [...draftData.blueBans, ...draftData.redBans].join(',') 
            }
          });
          setSuggestions(res.data);
        } catch (err) {
          console.error("AI Coach đang bận...");
        }
      };
      fetchAi();
    }
  }, [currentStepIdx, userSide, draftData]);

  // Lắng nghe sự thay đổi của danh sách Pick
    useEffect(() => {
    // Nếu cả 2 đội đều đã pick đủ 5 người -> Gọi API Phân tích
    if (draftData.bluePicks.length === 5 && draftData.redPicks.length === 5 && !analysisResult) {
      const fetchAnalysis = async () => {
        try {
          const your_team = userSide === 'Blue' ? draftData.bluePicks.join(',') : draftData.redPicks.join(',');
          const enemy_team = userSide === 'Blue' ? draftData.redPicks.join(',') : draftData.bluePicks.join(',');

          console.log("Đang gửi đội hình cho AI phân tích..."); // Báo log ra F12

          const response = await axios.get('http://localhost:8000/analyze', {
            params: { your_team, enemy_team }
          });
          
          if (response.data.status === 'success') {
            setAnalysisResult(response.data.analysis);
          }
        } catch (error) {
          console.error("Lỗi khi gọi API phân tích:", error);
        }
      };
      fetchAnalysis();
    }
  }, [draftData, userSide, analysisResult]); // Đổi thành giám sát TẤT CẢ draftData

const handleSelectHero = (heroName) => {
    pickSound.currentTime = 0; 
    pickSound.play().catch(err => console.log("Chưa tương tác với web: ", err));
    
    // Nếu tướng đã bị chọn/cấm thì không cho chọn lại
    if (isHeroUnavailable(heroName)) return;
    
    const step = DRAFT_STEPS[currentStepIdx];
    if (!step) return;

    // COPY SÂU (Deep Copy) để React phát hiện mảng thay đổi 100%
    const newData = { 
      bluePicks: [...draftData.bluePicks], 
      redPicks: [...draftData.redPicks], 
      blueBans: [...draftData.blueBans], 
      redBans: [...draftData.redBans] 
    };

    if (step.type === 'BAN') {
      step.side === 'Blue' ? newData.blueBans.push(heroName) : newData.redBans.push(heroName);
    } else {
      step.side === 'Blue' ? newData.bluePicks.push(heroName) : newData.redPicks.push(heroName);
    }

    setDraftData(newData);
    setCurrentStepIdx(currentStepIdx + 1);
    setSuggestions({ pick_suggestions: [], ban_suggestions: [] });
  };

  if (!userSide) {
    return (
      <div className="start-screen">
        <div className="overlay">
          <div className="logo-container">
            <h1>AOV AI COACH</h1>
            <p>Hệ thống phân tích & cấm chọn AOV</p>
          </div>
          
          <div className="side-buttons">
            <div className="side-card blue-card" onClick={() => setUserSide('Blue')}>
              <h2>ĐỘI XANH</h2>
              <span>Chọn trước (First Pick)</span>
            </div>
            
            <div className="vs-badge">VS</div>
            
            <div className="side-card red-card" onClick={() => setUserSide('Red')}>
              <h2>ĐỘI ĐỎ</h2>
              <span>Chọn sau (Counter Pick)</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const currentStep = DRAFT_STEPS[currentStepIdx] || { label: 'HOÀN TẤT', side: 'NONE' };
   
  
    
  return (
    <div className="draft-board">
      {/* Header: Hiển thị tướng Cấm bằng ảnh */}
      <div className="ban-header">
        <div className="ban-side blue">
          {draftData.blueBans.map((h, i) => (
            <div key={i} className="ban-icon-wrapper">
              <img src={getHeroAvatar(h)} alt={h} />
              <div className="ban-line"></div>
            </div>
          ))}
        </div>
        <div className="status-center">
          <div className="phase-label">{currentStep.label}</div>
          <div className="timer">15</div>
        </div>
        <div className="ban-side red">
          {draftData.redBans.map((h, i) => (
            <div key={i} className="ban-icon-wrapper">
              <img src={getHeroAvatar(h)} alt={h} />
              <div className="ban-line"></div>
            </div>
          ))}
        </div>
      </div>

      <div className="main-draft">
        {/* Picks Team Xanh */}
        <div className="pick-column blue-side">
        {[...Array(5)].map((_, i) => {
            const heroName = draftData.bluePicks[i];
            const isActive = currentStep.side === 'Blue' && currentStep.type === 'PICK' && draftData.bluePicks.length === i;
            return (
            <div key={i} className={`pick-slot ${isActive ? 'active' : ''}`}>
                {heroName ? (
                <div className="picked-info">
                    <img src={getHeroAvatar(heroName)} alt="" />
                    <span>{heroName}</span>
                </div>
                ) : <div className="placeholder" style={{paddingLeft: '15px', color: '#333'}}>SELECTING...</div>}
            </div>
            );
        })}
        </div>

        {/* CENTER PANEL: NƠI ĐIỀU PHỐI GIAO DIỆN */}
        <div className="center-panel">
          {analysisResult ? (
            // BẢNG TỔNG KẾT SAU KHI HOÀN TẤT DRAFT
            <div className="analysis-dashboard">
              <h2 className="dashboard-title">📊 PHÂN TÍCH ĐỘI HÌNH</h2>
              
              <div className="win-rate-section">
                <div className="team-stat blue-stat">
                  <span className="stat-label">Đội Xanh</span>
                  <span className="playstyle-tag">{userSide === 'Blue' ? analysisResult.your_team.playstyle : analysisResult.enemy_team.playstyle}</span>
                  <span className="wr-number">{userSide === 'Blue' ? analysisResult.your_team.win_probability : analysisResult.enemy_team.win_probability}%</span>
                </div>
                
                <div className="vs-circle">VS</div>
                
                <div className="team-stat red-stat">
                  <span className="stat-label">Đội Đỏ</span>
                  <span className="playstyle-tag">{userSide === 'Red' ? analysisResult.your_team.playstyle : analysisResult.enemy_team.playstyle}</span>
                  <span className="wr-number">{userSide === 'Red' ? analysisResult.your_team.win_probability : analysisResult.enemy_team.win_probability}%</span>
                </div>
              </div>

              <div className="coach-summary-box">
                <h3>🗣️ LỜI KHUYÊN TỪ HUẤN LUYỆN VIÊN</h3>
                <p>{analysisResult.coach_summary}</p>
              </div>
              
              <button className="reset-btn" onClick={() => window.location.reload()}>
                🔄 TRẬN MỚI
              </button>
            </div>
          ) : (
            // LƯỚI TƯỚNG VÀ GỢI Ý (Hiển thị trong lúc Draft)
            <>
              {/* Khu vực Gợi ý */}
              <div className={`ai-coach-panel ${currentStep.side === userSide ? 'visible' : 'hidden'}`}>
                  <h3>💡 AI SUGGESTIONS ({currentStep.type})</h3>
                  <div className="suggest-grid">
                  {(currentStep.type === 'PICK' ? suggestions.pick_suggestions : suggestions.ban_suggestions).map((s, i) => (
                      <div key={i} className="suggest-card" onClick={() => handleSelectHero(s.hero)}>
                      <img src={getHeroAvatar(s.hero)} alt="" />
                      <div className="s-info">
                          <p className="s-hero">{s.hero}</p>
                          <p className="s-reason">{s.reason}</p>
                          <span className="s-score">{s.score}% WR</span>
                      </div>
                      </div>
                  ))}
                  </div>
              </div>

              {/* Thanh tìm kiếm */}
              <div className="search-container">
                  <input 
                  type="text" 
                  placeholder="Tìm tên tướng..." 
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="search-input"
                  />
              </div>
              
              {/* Grid Tướng */}
              <div className="hero-grid">
                  {filteredHeroes.map((hero) => (
                  <div 
                      key={hero.id} 
                      className={`hero-item ${isHeroUnavailable(hero.name) ? 'disabled' : ''}`} 
                      onClick={() => handleSelectHero(hero.name)}
                  >
                      <img src={`/assets/heroes/${hero.keyword.toLowerCase()}.jpg`} alt={hero.name} />
                      <span>{hero.name}</span>
                  </div>
                  ))}
              </div>
            </>
          )}
        </div>

        {/* Picks Team Đỏ */}
        <div className="pick-column red-side">
          {[...Array(5)].map((_, i) => (
            <div key={i} className={`pick-slot ${currentStep.side === 'Red' && currentStep.type === 'PICK' && draftData.redPicks.length === i ? 'active' : ''}`}>
               {draftData.redPicks[i] ? (
                 <div className="picked-info reverse">
                   <span>{draftData.redPicks[i]}</span>
                   <img src={getHeroAvatar(draftData.redPicks[i])} alt="hero" />
                 </div>
               ) : <div className="placeholder" style={{paddingRight: '15px', color: '#333'}}>SELECTING...</div>}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default App;