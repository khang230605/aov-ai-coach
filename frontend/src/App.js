import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { DRAFT_STEPS } from './constants';
import './App.css';
import heroesData from './heroes.json';

const pickSound = new Audio('/assets/sounds/pick.mp3');
pickSound.volume = 0.7;

function App() {
  // 1. Hàm hỗ trợ tải dữ liệu từ thẻ nhớ (LocalStorage) cực an toàn
  const loadState = (key, defaultValue) => {
    try {
      const saved = localStorage.getItem(key);
      return saved !== null ? JSON.parse(saved) : defaultValue;
    } catch (e) {
      return defaultValue;
    }
  };

  // 2. Khai báo State và nạp dữ liệu từ LocalStorage (nếu có)
  const [inSeries, setInSeries] = useState(() => loadState('aov_inSeries', false));
  const [gameNumber, setGameNumber] = useState(() => loadState('aov_gameNumber', 1));
  const [myTeamUsed, setMyTeamUsed] = useState(() => loadState('aov_myTeamUsed', []));
  const [enemyTeamUsed, setEnemyTeamUsed] = useState(() => loadState('aov_enemyTeamUsed', []));

  const [userSide, setUserSide] = useState(() => loadState('aov_userSide', null));
  const [currentStepIdx, setCurrentStepIdx] = useState(() => loadState('aov_currentStepIdx', 0));
  const [draftData, setDraftData] = useState(() => loadState('aov_draftData', {
    bluePicks: [], redPicks: [], blueBans: [], redBans: []
  }));

  const [suggestions, setSuggestions] = useState({ pick_suggestions: [], ban_suggestions: [] });
  const [analysisResult, setAnalysisResult] = useState(() => loadState('aov_analysis', null));
  const [searchTerm, setSearchTerm] = useState("");

  // 3. TỰ ĐỘNG LƯU MỌI THAY ĐỔI XUỐNG THẺ NHỚ
  useEffect(() => {
    localStorage.setItem('aov_inSeries', JSON.stringify(inSeries));
    localStorage.setItem('aov_gameNumber', JSON.stringify(gameNumber));
    localStorage.setItem('aov_myTeamUsed', JSON.stringify(myTeamUsed));
    localStorage.setItem('aov_enemyTeamUsed', JSON.stringify(enemyTeamUsed));
    localStorage.setItem('aov_userSide', JSON.stringify(userSide));
    localStorage.setItem('aov_currentStepIdx', JSON.stringify(currentStepIdx));
    localStorage.setItem('aov_draftData', JSON.stringify(draftData));
    localStorage.setItem('aov_analysis', JSON.stringify(analysisResult));
  }, [inSeries, gameNumber, myTeamUsed, enemyTeamUsed, userSide, currentStepIdx, draftData, analysisResult]);

  const normalizeName = (str) => {
    if (!str) return '';
    return str.toLowerCase().replace(/[^a-z0-9]/g, '');
  };

  const getHeroAvatar = (name) => {
    if (!name) return null;
    const hero = heroesData.find(h => normalizeName(h.name) === normalizeName(name));
    const keyword = hero ? hero.keyword.toLowerCase() : 'default';
    return `/assets/heroes/${keyword}.jpg`;
  };

  const filteredHeroes = heroesData.filter(hero => 
    hero.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    hero.keyword.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // --- LOGIC KIỂM TRA TƯỚNG BỊ KHÓA (GLOBAL BAN-PICK) ---
  const isHeroUnavailable = (heroName) => {
    // 1. Khóa nếu đã được chọn/cấm trong ván này
    const allSelectedThisGame = [...draftData.bluePicks, ...draftData.redPicks, ...draftData.blueBans, ...draftData.redBans];
    if (allSelectedThisGame.includes(heroName)) return true;

    const step = DRAFT_STEPS[currentStepIdx];
    if (!step) return false;

    const isMyTurn = step.side === userSide;

    if (isMyTurn) {
      // Lượt của mình: Không được PICK tướng mình đã dùng ở ván trước
      if (step.type === 'PICK' && myTeamUsed.includes(heroName)) return true;
      // Không nên BAN tướng địch đã dùng (vì địch không thể pick nữa, cấm là lãng phí)
      if (step.type === 'BAN' && enemyTeamUsed.includes(heroName)) return true;
    } else {
      // Lượt của địch: Địch không được PICK tướng địch đã dùng
      if (step.type === 'PICK' && enemyTeamUsed.includes(heroName)) return true;
      // Địch không cần BAN tướng mình đã dùng
      if (step.type === 'BAN' && myTeamUsed.includes(heroName)) return true;
    }

    return false;
  };

  // Gọi AI Gợi ý (Truyền thêm lịch sử tướng đã dùng)
  useEffect(() => {
    const currentStep = DRAFT_STEPS[currentStepIdx];
    if (userSide && currentStep && currentStep.side === userSide) {
      const fetchAi = async () => {
        try {
          const res = await axios.get(`https://aov-backend-khang.onrender.com/draft`, {
            params: { 
              your_team: (userSide === 'Blue' ? draftData.bluePicks : draftData.redPicks).join(','), 
              enemy_team: (userSide === 'Blue' ? draftData.redPicks : draftData.bluePicks).join(','), 
              bans: [...draftData.blueBans, ...draftData.redBans].join(','),
              your_used: myTeamUsed.join(','),     // Bơm data lịch sử vào đây
              enemy_used: enemyTeamUsed.join(',')  // Bơm data lịch sử vào đây
            }
          });
          setSuggestions(res.data);
        } catch (err) {
          console.error("AI Coach đang bận...");
        }
      };
      fetchAi();
    }
  }, [currentStepIdx, userSide, draftData, myTeamUsed, enemyTeamUsed]);

  // Gọi Phân tích Đội hình khi pick xong
  useEffect(() => {
    if (draftData.bluePicks.length === 5 && draftData.redPicks.length === 5 && !analysisResult) {
      const fetchAnalysis = async () => {
        try {
          const your_team = userSide === 'Blue' ? draftData.bluePicks.join(',') : draftData.redPicks.join(',');
          const enemy_team = userSide === 'Blue' ? draftData.redPicks.join(',') : draftData.bluePicks.join(',');

          const response = await axios.get('https://aov-backend-khang.onrender.com/analyze', {
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
  }, [draftData, userSide, analysisResult]);

  const handleSelectHero = (heroName) => {
    pickSound.currentTime = 0; 
    pickSound.play().catch(err => console.log("Audio play error", err));
    
    if (isHeroUnavailable(heroName)) return;
    
    const step = DRAFT_STEPS[currentStepIdx];
    if (!step) return;

    const newData = { 
      bluePicks: [...draftData.bluePicks], redPicks: [...draftData.redPicks], 
      blueBans: [...draftData.blueBans], redBans: [...draftData.redBans] 
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

  // --- CÁC HÀM ĐIỀU KHIỂN BO ĐẤU ---
  const handleStartSeries = () => setInSeries(true);

  const handleNextGame = () => {
    // Lưu lại tướng đã dùng của Game vừa rồi
    const myPicks = userSide === 'Blue' ? draftData.bluePicks : draftData.redPicks;
    const enemyPicks = userSide === 'Blue' ? draftData.redPicks : draftData.bluePicks;
    
    setMyTeamUsed([...myTeamUsed, ...myPicks]);
    setEnemyTeamUsed([...enemyTeamUsed, ...enemyPicks]);

    // Reset bàn Draft để chuẩn bị Game mới
    setDraftData({ bluePicks: [], redPicks: [], blueBans: [], redBans: [] });
    setCurrentStepIdx(0);
    setUserSide(null);
    setAnalysisResult(null);
    setSuggestions({ pick_suggestions: [], ban_suggestions: [] });
    
    // Tăng số đếm Game
    setGameNumber(gameNumber + 1);
  };

const handleEndSeries = () => {
    // Xóa sạch bộ nhớ LocalStorage
    localStorage.removeItem('aov_inSeries');
    localStorage.removeItem('aov_gameNumber');
    localStorage.removeItem('aov_myTeamUsed');
    localStorage.removeItem('aov_enemyTeamUsed');
    localStorage.removeItem('aov_userSide');
    localStorage.removeItem('aov_currentStepIdx');
    localStorage.removeItem('aov_draftData');
    localStorage.removeItem('aov_analysis');

    // Reset State trên màn hình về ban đầu
    setInSeries(false);
    setGameNumber(1);
    setMyTeamUsed([]);
    setEnemyTeamUsed([]);
    setDraftData({ bluePicks: [], redPicks: [], blueBans: [], redBans: [] });
    setCurrentStepIdx(0);
    setUserSide(null);
    setAnalysisResult(null);
    setSuggestions({ pick_suggestions: [], ban_suggestions: [] });
  };

  // MÀN HÌNH 1: TẠO TRẬN ĐẤU MỚI
  if (!inSeries) {
    return (
      <>
        <div className="rotate-warning">
          <div className="rotate-icon">📱 🔄</div>
          <h2>Vui lòng xoay ngang thiết bị</h2>
          <p>Giao diện cấm chọn chuẩn Esports được thiết kế tối ưu nhất cho màn hình ngang.</p>
        </div>
        <div className="start-screen">
          <div className="overlay">
            <div className="logo-container">
              <h1>AOV COACH - KHANG's AI</h1>
              <p>Hệ thống phân tích & cấm chọn Liên Quân Mobile</p>
            </div>
            <button className="btn-create-match" onClick={handleStartSeries}>
              BẮT ĐẦU TRẬN ĐẤU
            </button>
          </div>
        </div>
      </>
    );
  }

  // MÀN HÌNH 2: CHỌN PHE CHO GAME HIỆN TẠI
  if (!userSide) {
    return (
      <>
        <div className="rotate-warning">
          <div className="rotate-icon">📱 🔄</div>
          <h2>Vui lòng xoay ngang thiết bị</h2>
        </div>
        <div className="start-screen">
          <div className="overlay">
            <div className="logo-container">
              <h1>GAME {gameNumber}</h1>
              <p>Luật Global Ban Pick: Tướng đã dùng sẽ bị khóa</p>
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
      </>
    );
  }

  const currentStep = DRAFT_STEPS[currentStepIdx] || { label: 'HOÀN TẤT', side: 'NONE' };
   
  return (
    <>
      <div className="rotate-warning">
        <div className="rotate-icon">📱 🔄</div>
        <h2>Vui lòng xoay ngang thiết bị</h2>
      </div>

      <div className="draft-board">
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
            <div className="phase-label">GAME {gameNumber} - {currentStep.label}</div>
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

          <div className="center-panel">
            {analysisResult ? (
              // BẢNG TỔNG KẾT VÀ NÚT ĐIỀU HƯỚNG BO ĐẤU
              <div className="analysis-dashboard">
                <h2 className="dashboard-title">📊 PHÂN TÍCH ĐỘI HÌNH GAME {gameNumber}</h2>
                
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
                
                {/* NÚT TIẾP TỤC HOẶC KẾT THÚC SERIES */}
                <div className="action-buttons">
                  <button className="btn-next-game" onClick={handleNextGame}>
                    ⏭️ TIẾP TỤC GAME {gameNumber + 1}
                  </button>
                  <button className="reset-btn" onClick={handleEndSeries}>
                    ⏹ KẾT THÚC BO ĐẤU
                  </button>
                </div>
              </div>
            ) : (
              // LƯỚI TƯỚNG VÀ GỢI Ý
              <>
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

                <div className="search-container">
                    <input type="text" placeholder="Tìm tên tướng..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} className="search-input" />
                </div>
                
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
    </>
  );
}

export default App;