import pickle
import os
import sys

try:
    with open('backend/app/models/best_live_model.pkl', 'rb') as f:
        data = pickle.load(f)
    print(data.keys())
    print("Features:", data.get('features'))
    model = data.get('model')
    print("Model Type:", type(model))
except Exception as e:
    print("Error:", e)
