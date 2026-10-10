import os
import sys
import json
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

base_dir = r"C:\Users\gokul\Desktop\PROJECTS\climatetwin"
sys.path.insert(0, os.path.join(base_dir, 'backend'))

from app.core.asset_risk import asset_risk_engine
from app.core.multihazard import multihazard_engine

def run_asset_risk_evaluation():
    print("=== Phase 14: Asset-Level Infrastructure Risk & Vulnerability Mapping Evaluation ===")
    
    ar_dir = os.path.join(base_dir, 'docs', 'asset_risk')
    plots_dir = os.path.join(base_dir, 'docs', 'plots')
    os.makedirs(ar_dir, exist_ok=True)
    os.makedirs(plots_dir, exist_ok=True)
    
    # 1. Asset Inventory
    print("\n[Step 1] Building Asset Inventory...")
    inv_data = []
    for a in asset_risk_engine.ASSETS:
        inv_data.append({
            'Asset_ID': a['asset_id'],
            'Code': a['code'],
            'Name': a['name'],
            'Asset_Type': a['asset_type'],
            'Latitude': a['lat'],
            'Longitude': a['lon'],
            'DEM_Elevation_m': a['dem_elevation_m'],
            'Capacity_mcft': a['capacity_mcft'],
            'Criticality': a['criticality'],
            'Criticality_Weight': a['criticality_weight'],
            'Upstream_Of': ', '.join(a['upstream_of']) if a['upstream_of'] else 'None'
        })
    df_inv = pd.DataFrame(inv_data)
    df_inv.to_csv(os.path.join(ar_dir, 'asset_inventory.csv'), index=False)
    print(f"Saved asset inventory ({len(df_inv)} assets) to asset_inventory.csv")
    
    # 2. Asset Risk Assessment Across Benchmark Deluge State
    print("\n[Step 2] Evaluating Asset Risk Across Chennai Catchment...")
    deluge_state = {
        'rainfall_daily': 95.0,
        'rainfall_rate_1h': 14.0,
        'total_reservoir_level': 10200.0,
        'reservoir_fill_ratio': 0.906,
        'temp_max': 27.0,
        'dew_point_mean': 24.5,
        'wind_speed_mean': 12.0,
        'elevation_m': 6.0
    }
    compound_deluge = multihazard_engine.calculate_compound_risk(deluge_state, flood_prob=0.85)
    
    ranked_assets = asset_risk_engine.assess_all_assets(deluge_state)
    with open(os.path.join(ar_dir, 'asset_risk_results.json'), 'w') as f:
        json.dump(ranked_assets, f, indent=2)
        
    for a in ranked_assets:
        print(f"  -> Rank {a['priority_rank']}: {a['code']} ({a['asset_type']}) - ARI: {a['asset_risk_index']:.3f} [{a['risk_level']}] - Elev: {a['dem_elevation_m']}m")
        
    # 3. Top Priority Ranking
    top_priority = asset_risk_engine.get_top_priority_assets(limit=3, env_state=deluge_state)
    with open(os.path.join(ar_dir, 'asset_priority_ranking.json'), 'w') as f:
        json.dump(top_priority, f, indent=2)
        
    # 4. Spatial Exposure & Vulnerability Breakdown
    exp_data = [{
        'code': a['code'],
        'exposure_score': a['exposure_score'],
        'vulnerability_proxy': a['vulnerability_proxy'],
        'criticality_weight': a['criticality_weight'],
        'dem_elevation_m': a['dem_elevation_m']
    } for a in ranked_assets]
    with open(os.path.join(ar_dir, 'asset_exposure.json'), 'w') as f:
        json.dump(exp_data, f, indent=2)

    # 5. Generate 6-Panel Research Evaluation Graphics
    print("\n[Step 5] Generating 6-Panel Research Evaluation Graphics...")
    fig = plt.figure(figsize=(18, 12))
    
    # Panel 1: Asset Risk Index (ARI) Sorted by Priority Rank
    ax1 = fig.add_subplot(2, 3, 1)
    codes = [a['code'].replace('_', '\n') for a in ranked_assets]
    aris = [a['asset_risk_index'] for a in ranked_assets]
    colors = ['#EF4444' if a['risk_level'] == 'CRITICAL' else '#F97316' if a['risk_level'] == 'HIGH' else '#F59E0B' for a in ranked_assets]
    
    ax1.bar(codes, aris, color=colors, alpha=0.85, edgecolor='black')
    ax1.axhline(0.75, color='red', linestyle='--', label='Critical Threshold (0.75)')
    ax1.axhline(0.50, color='orange', linestyle='--', label='High Threshold (0.50)')
    ax1.set_ylabel('Asset Risk Index (ARI)', fontsize=10, fontweight='bold')
    ax1.set_title('1. Prioritized Asset Risk Ranking (Deluge Scenario)', fontsize=11, fontweight='bold')
    ax1.set_ylim(0, 1.15)
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='upper right', fontsize=8.5)
    
    # Panel 2: Multi-Factor Component Comparison (H, E, V_proxy, C)
    ax2 = fig.add_subplot(2, 3, 2)
    top_4 = ranked_assets[:4]
    t4_codes = [a['code'].replace('_', '\n') for a in top_4]
    x = np.arange(len(top_4))
    w = 0.20
    
    h_vals = [a['hazard_score'] for a in top_4]
    e_vals = [a['exposure_score'] for a in top_4]
    v_vals = [a['vulnerability_proxy'] for a in top_4]
    c_vals = [a['criticality_weight'] for a in top_4]
    
    ax2.bar(x - 1.5*w, h_vals, width=w, label='Hazard (H)', color='#EF4444', alpha=0.85, edgecolor='black')
    ax2.bar(x - 0.5*w, e_vals, width=w, label='Exposure (E)', color='#3B82F6', alpha=0.85, edgecolor='black')
    ax2.bar(x + 0.5*w, v_vals, width=w, label='Vuln Proxy (V)', color='#F59E0B', alpha=0.85, edgecolor='black')
    ax2.bar(x + 1.5*w, c_vals, width=w, label='Criticality (C)', color='#8B5CF6', alpha=0.85, edgecolor='black')
    
    ax2.set_xticks(x)
    ax2.set_xticklabels(t4_codes, fontweight='bold')
    ax2.set_ylabel('Normalized Component Factor [0, 1]', fontsize=10, fontweight='bold')
    ax2.set_title('2. Factor Decomposition (Top 4 Critical Assets)', fontsize=11, fontweight='bold')
    ax2.set_ylim(0, 1.2)
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc='upper right', fontsize=8)
    
    # Panel 3: DEM Elevation vs Vulnerability Proxy
    ax3 = fig.add_subplot(2, 3, 3)
    elevs = [a['dem_elevation_m'] for a in ranked_assets]
    v_proxies = [a['vulnerability_proxy'] for a in ranked_assets]
    
    for a in ranked_assets:
        ax3.scatter(a['dem_elevation_m'], a['vulnerability_proxy'], s=120, color='#3B82F6', edgecolor='black', zorder=5)
        ax3.annotate(a['code'], (a['dem_elevation_m']+0.8, a['vulnerability_proxy']-0.02), fontsize=8, fontweight='bold')
        
    ax3.set_xlabel('Copernicus DEM 30m Elevation (m)', fontsize=10, fontweight='bold')
    ax3.set_ylabel('Topographic Vulnerability Proxy (V_proxy)', fontsize=10, fontweight='bold')
    ax3.set_title('3. Topographic Depression vs Vulnerability Proxy', fontsize=11, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    
    # Panel 4: Cascading Spillway Surge: Chembarambakkam -> Adyar Outfall
    ax4 = fig.add_subplot(2, 3, 4)
    fill_levels = np.linspace(0.4, 1.0, 7)
    chem_aris = []
    adyar_aris = []
    for f in fill_levels:
        st = deluge_state.copy()
        st['reservoir_fill_ratio'] = f
        chem_aris.append(asset_risk_engine.evaluate_asset_risk(asset_risk_engine.ASSETS[3], st, compound_deluge)['asset_risk_index'])
        adyar_aris.append(asset_risk_engine.evaluate_asset_risk(asset_risk_engine.ASSETS[4], st, compound_deluge)['asset_risk_index'])
        
    ax4.plot(fill_levels * 100, chem_aris, marker='s', label='Chembarambakkam (Upstream Reservoir)', color='#3B82F6', lw=2)
    ax4.plot(fill_levels * 100, adyar_aris, marker='o', label='Adyar Outfall (Downstream Estuary)', color='#EF4444', lw=2)
    ax4.axvline(85.0, color='red', linestyle='--', label='Emergency Spillway Threshold (85%)')
    ax4.set_xlabel('Chembarambakkam Storage Capacity Fill (%)', fontsize=10, fontweight='bold')
    ax4.set_ylabel('Asset Risk Index (ARI)', fontsize=10, fontweight='bold')
    ax4.set_title('4. Cascading Upstream Spillway -> Downstream Estuary Risk', fontsize=11, fontweight='bold')
    ax4.grid(True, alpha=0.3)
    ax4.legend(loc='lower right', fontsize=8.5)
    
    # Panel 5: Multi-Horizon Forecast Risk Progression (Top 4 Assets)
    ax5 = fig.add_subplot(2, 3, 5)
    horizons = ['Current', '+15m', '+30m', '+60m']
    for a in top_4:
        fc = [a['forecast_risk']['current'], a['forecast_risk']['15m'], a['forecast_risk']['30m'], a['forecast_risk']['60m']]
        ax5.plot(horizons, fc, marker='o', label=a['code'], lw=2)
        
    ax5.set_ylabel('Forecast Asset Risk Index (ARI)', fontsize=10, fontweight='bold')
    ax5.set_title('5. Multi-Horizon Forecast Risk Progression', fontsize=11, fontweight='bold')
    ax5.set_ylim(0.4, 1.05)
    ax5.grid(True, alpha=0.3)
    ax5.legend(loc='lower right', fontsize=8)
    
    # Panel 6: Spatial Coordinates & Risk Level Mapping
    ax6 = fig.add_subplot(2, 3, 6)
    for a in ranked_assets:
        color = '#EF4444' if a['risk_level'] == 'CRITICAL' else '#F97316' if a['risk_level'] == 'HIGH' else '#F59E0B'
        ax6.scatter(a['coordinates']['lon'], a['coordinates']['lat'], s=150, color=color, edgecolor='black', zorder=5)
        ax6.annotate(f"{a['code']}\n({a['risk_level']})", (a['coordinates']['lon']+0.015, a['coordinates']['lat']-0.01), fontsize=8, fontweight='bold')
        
    ax6.set_xlabel('Longitude (°E)', fontsize=10, fontweight='bold')
    ax6.set_ylabel('Latitude (°N)', fontsize=10, fontweight='bold')
    ax6.set_title('6. Spatial Asset Risk Distribution across Greater Chennai', fontsize=11, fontweight='bold')
    ax6.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plot_path = os.path.join(plots_dir, 'phase14_asset_risk_evaluation.png')
    plt.savefig(plot_path, dpi=200)
    plt.close()
    print(f"Saved asset risk evaluation plot to {plot_path}")
    
    # 6. Generate Research Markdown Report
    print("\n[Step 6] Generating Research Markdown Report...")
    report_md = f"""# ClimateTwin Phase 14: Asset-Level Infrastructure Risk & Vulnerability Report

## 1. Research Motivation
Hazard predictions are operationally actionable only when tied to specific urban infrastructure assets. Phase 14 connects compound hazard states to **8 verified critical infrastructure assets** across Greater Chennai.

## 2. Mandatory Methodological Distinction
- **Hazard ($H$)**: Environmental intensity (from Phase 13 $CRS$).
- **Exposure ($E$)**: Geographic and hydrological catchment proximity.
- **Vulnerability Proxy ($V_{{\\text{{proxy}}}}$)**: Topographic depression ($<10\\text{{m}}$) and structural type sensitivity.
- **Criticality ($C$)**: Systemic urban societal importance.

$$ARI = H \\cdot 0.35 + E \\cdot 0.30 + V_{{\\text{{proxy}}}} \\cdot 0.20 + C \\cdot 0.15 + \\text{{Cascade Bonus}} \\in [0.0, 1.0]$$

## 3. Prioritized Action Queue (Deluge Benchmark)
1. **{ranked_assets[0]['name']}**: ARI = {ranked_assets[0]['asset_risk_index']:.3f} [{ranked_assets[0]['risk_level']}] &bull; Elev: {ranked_assets[0]['dem_elevation_m']}m
2. **{ranked_assets[1]['name']}**: ARI = {ranked_assets[1]['asset_risk_index']:.3f} [{ranked_assets[1]['risk_level']}] &bull; Elev: {ranked_assets[1]['dem_elevation_m']}m
3. **{ranked_assets[2]['name']}**: ARI = {ranked_assets[2]['asset_risk_index']:.3f} [{ranked_assets[2]['risk_level']}] &bull; Elev: {ranked_assets[2]['dem_elevation_m']}m

## 4. Research Transparency & Categorization
- **OBSERVED**: NASA IMERG rainfall, CMWSSB storage levels, NOAA ISD weather.
- **DERIVED**: Copernicus DEM 30m elevations, normalized exposure indices.
- **MODEL-PREDICTED**: Random Forest flood probabilities & multi-horizon forecasts.
- **RULE-BASED**: Criticality weights & operational decision support actions.
- **TRANSPARENT PROXY**: Topographic vulnerability proxy ($V_{{\\text{{proxy}}}}$).
"""
    with open(os.path.join(ar_dir, 'asset_validation_report.md'), 'w', encoding='utf-8') as f:
        f.write(report_md)
    print("Saved validation report to asset_validation_report.md")
    print("\n=== Phase 14 Asset Risk Evaluation Complete ===")

if __name__ == '__main__':
    run_asset_risk_evaluation()
