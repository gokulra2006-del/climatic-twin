import pandas as pd
df = pd.read_csv('data/processed/catalogue_v1/train_split.csv')
print('Train max date:', df['time'].max())
df = pd.read_csv('data/processed/catalogue_v1/val_split.csv')
print('Val max date:', df['time'].max())
