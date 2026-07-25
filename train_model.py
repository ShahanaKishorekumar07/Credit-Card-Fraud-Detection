import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import IsolationForest
from sklearn.metrics import accuracy_score
import joblib


data = pd.read_csv('creditcard.csv')


X = data.drop('Class', axis=1)
y = data['Class']


X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)


rf = RandomForestClassifier(n_estimators=100)
rf.fit(X_train, y_train)


iso = IsolationForest(contamination=0.01)
iso.fit(X_train)


joblib.dump(rf, 'fraud_model.pkl')
joblib.dump(iso, 'anomaly_model.pkl')


pred = rf.predict(X_test)
print("Accuracy:", accuracy_score(y_test, pred))