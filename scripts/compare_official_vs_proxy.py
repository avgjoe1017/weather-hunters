"""
Compare Official NOAA data vs Open-Meteo Proxy

Shows how accurate our proxy data was compared to the real thing.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd

# Load both datasets
official = pd.read_csv(project_root / 'data' / 'weather' / 'nws_settlement_ground_truth_OFFICIAL.csv')
proxy = pd.read_csv(project_root / 'data' / 'weather' / 'nws_settlement_ground_truth.csv')

# Merge on city and date
merged = official.merge(proxy, on=['city', 'date'], suffixes=('_official', '_proxy'))

print('=' * 70)
print('OFFICIAL vs PROXY COMPARISON')
print('=' * 70)
print()

# Calculate differences
merged['temp_diff'] = abs(merged['nws_settlement_temp_official'] - merged['nws_settlement_temp_proxy'])

print(f'Total matched records: {len(merged)}')
print()

print('Temperature Difference Statistics:')
print(f'  Mean difference: {merged["temp_diff"].mean():.2f}F')
print(f'  Median difference: {merged["temp_diff"].median():.2f}F')
print(f'  Max difference: {merged["temp_diff"].max():.0f}F')
print()

print('Accuracy of Proxy Data:')
exact = (merged['temp_diff'] == 0).sum()
exact_pct = (merged['temp_diff'] == 0).mean() * 100
within_1 = (merged['temp_diff'] <= 1).sum()
within_1_pct = (merged['temp_diff'] <= 1).mean() * 100
within_2 = (merged['temp_diff'] <= 2).sum()
within_2_pct = (merged['temp_diff'] <= 2).mean() * 100
within_3 = (merged['temp_diff'] <= 3).sum()
within_3_pct = (merged['temp_diff'] <= 3).mean() * 100

print(f'  Exact match (0F diff): {exact} ({exact_pct:.1f}%)')
print(f'  Within 1F: {within_1} ({within_1_pct:.1f}%)')
print(f'  Within 2F: {within_2} ({within_2_pct:.1f}%)')
print(f'  Within 3F: {within_3} ({within_3_pct:.1f}%)')
print()

print('By City:')
for city in sorted(merged['city'].unique()):
    city_data = merged[merged['city'] == city]
    exact = (city_data['temp_diff'] == 0).mean() * 100
    within_2 = (city_data['temp_diff'] <= 2).mean() * 100
    mean_diff = city_data['temp_diff'].mean()
    print(f'  {city}: {exact:.1f}% exact, {within_2:.1f}% within 2F, avg diff {mean_diff:.2f}F')

print()
print('=' * 70)
print()

if exact_pct > 90:
    print('[OK] Proxy was EXCELLENT (>90% exact match)')
    print('     Using official data will improve slightly')
elif exact_pct > 80:
    print('[OK] Proxy was VERY GOOD (>80% exact match)')
    print('     Using official data will improve accuracy')
elif within_2_pct > 95:
    print('[~] Proxy was GOOD (>95% within 2F)')
    print('    Using official data is important for precision')
else:
    print('[!] Proxy had significant differences')
    print('    Using official data is CRITICAL')

print()
print('=' * 70)

