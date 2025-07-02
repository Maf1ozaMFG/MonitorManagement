import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib

# Загрузка данных
data = pd.read_csv('gesture_data.csv', header=None)
X = data.iloc[:, :-1]
y = data.iloc[:, -1]

# Разделение данных
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Обучение модели
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Оценка
print("Accuracy:", model.score(X_test, y_test))
joblib.dump(model, 'gesture_model.pkl')