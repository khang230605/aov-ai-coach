import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
import xgboost as xgb
import joblib
import os

def train_winrate_model():
    print("🧠 ĐANG TÌM KIẾM THUẬT TOÁN TỐI ƯU NHẤT...\n")

    try:
        df = pd.read_csv('data/ml_dataset.csv')
    except FileNotFoundError:
        print("❌ Không tìm thấy file data/ml_dataset.csv")
        return

    X = df.drop(columns=['Left_Win'])
    y = df['Left_Win']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # 1. Khởi tạo 3 "thí sinh" AI khác nhau
    models = {
        # Logistic Regression: Cực kỳ xuất sắc trong việc xử lý ma trận One-Hot nhiều số 0
        "Logistic Regression": LogisticRegression(C=0.5, class_weight='balanced', max_iter=1000, random_state=42),
        
        # Random Forest: Rừng quyết định, phân nhánh tốt, ít bị học vẹt hơn XGBoost ở data nhỏ
        "Random Forest": RandomForestClassifier(n_estimators=200, max_depth=10, min_samples_leaf=2, random_state=42),
        
        # XGBoost (Đã tinh chỉnh nhẹ lại)
        "XGBoost": xgb.XGBClassifier(n_estimators=100, learning_rate=0.05, max_depth=4, random_state=42)
    }

    best_model = None
    best_acc = 0
    best_name = ""

    # 2. Cho cả 3 thí sinh cùng đi thi
    for name, model in models.items():
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        
        acc = accuracy_score(y_test, y_pred)
        print(f"🔹 Thuật toán {name}:")
        print(f"   Độ chính xác: {acc * 100:.2f}%")
        
        # Lưu lại mô hình giỏi nhất
        if acc > best_acc:
            best_acc = acc
            best_model = model
            best_name = name

    print("\n==================================")
    print(f"🏆 NGƯỜI CHIẾN THẮNG: {best_name} với {best_acc * 100:.2f}%")
    print("==================================")

    # 3. Lưu mô hình tốt nhất lại
    os.makedirs('models', exist_ok=True)
    joblib.dump(best_model, 'models/draft_ai_model.joblib')
    joblib.dump(list(X.columns), 'models/feature_columns.joblib')
    print(f"💾 Đã lưu 'bộ não' của {best_name} làm hệ thống chính thức!")






if __name__ == "__main__":
    train_winrate_model()