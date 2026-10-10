import os
import sys
import json
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BASE_DIR = r"C:\Users\gokul\Desktop\PROJECTS\climatetwin"
SPATIAL_DIR = os.path.join(BASE_DIR, 'docs', 'spatial')
PLOT_DIR = os.path.join(BASE_DIR, 'docs', 'plots')
os.makedirs(SPATIAL_DIR, exist_ok=True)
os.makedirs(PLOT_DIR, exist_ok=True)

sys.path.insert(0, os.path.join(BASE_DIR, 'backend'))
from app.core.spatial_inundation import spatial_inundation_engine, SPATIAL_ZONES

def format_markdown_table(df: pd.DataFrame) -> str:
    headers = list(df.columns)
    lines = ["| " + " | ".join(headers) + " |"]
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(str(val) for val in row.values) + " |")
    return "\n".join(lines)

def evaluate_spatial_mapping():
    print("=================================================================")
    print("  CLIMATETWIN PHASE 15: SPATIAL INUNDATION & IMPACT EVALUATION")
    print("=================================================================\n")

    # Step 1: Generate Data Inventory CSV
    print("[1/6] Generating Spatial Data Inventory...")
    inventory_data = [
        {"Zone_ID": z["zone_id"], "Zone_Name": z["name"], "Catchment": z["catchment"],
         "Center_Lat": z["center"]["lat"], "Center_Lon": z["center"]["lon"],
         "DEM_Elevation_m": spatial_inundation_engine.get_dem_elevation(z["center"]["lat"], z["center"]["lon"]),
         "Drainage_Outlet": z["drainage_outlet"], "Urban_Density": z["urban_density_class"],
         "Historical_Vuln": z["historical_flood_vulnerability"],
         "Intersecting_Critical_Assets": ", ".join(z["critical_assets"])}
        for z in SPATIAL_ZONES
    ]
    df_inv = pd.DataFrame(inventory_data)
    inv_csv_path = os.path.join(SPATIAL_DIR, 'spatial_data_inventory.csv')
    df_inv.to_csv(inv_csv_path, index=False)
    print(f"  -> Saved inventory to {inv_csv_path}")

    # Step 2: Evaluate Standard & Storm Inundation States
    print("\n[2/6] Evaluating Spatial Susceptibility and Impact Indices...")
    monsoon_storm_state = {
        'rainfall_daily': 90.0,
        'runoff_indicator': 0.75,
        'flood_probability': 0.72,
        'reservoir_fill_ratio': 0.90
    }
    
    zone_results = spatial_inundation_engine.assess_all_zones(monsoon_storm_state)
    
    # Save terrain susceptibility JSON
    terrain_data = {
        z["zone_id"]: {
            "name": z["name"],
            "dem_elevation_m": z["dem_elevation_m"],
            "terrain_susceptibility": z["terrain_susceptibility"],
            "drainage_proximity_factor": round(1.0 - z["dem_elevation_m"]/30.0, 2)
        }
        for z in zone_results
    }
    with open(os.path.join(SPATIAL_DIR, 'terrain_susceptibility.json'), 'w') as f:
        json.dump(terrain_data, f, indent=2)

    # Save flood susceptibility JSON
    flood_susc_data = {
        z["zone_id"]: {
            "name": z["name"],
            "flood_susceptibility_index": z["flood_susceptibility_index"],
            "historical_vulnerability": next(s["historical_flood_vulnerability"] for s in SPATIAL_ZONES if s["zone_id"] == z["zone_id"])
        }
        for z in zone_results
    }
    with open(os.path.join(SPATIAL_DIR, 'flood_susceptibility.json'), 'w') as f:
        json.dump(flood_susc_data, f, indent=2)

    # Save full spatial impact results JSON
    with open(os.path.join(SPATIAL_DIR, 'spatial_impact_results.json'), 'w') as f:
        json.dump(zone_results, f, indent=2)

    # Save multi-horizon forecast results JSON
    forecast_data = {
        z["zone_id"]: {
            "name": z["name"],
            "current_sfii": z["spatial_flood_impact_index"],
            "forecast_progression": z["forecast_progression"],
            "prediction_interval": z["prediction_interval"]
        }
        for z in zone_results
    }
    with open(os.path.join(SPATIAL_DIR, 'spatial_forecast_results.json'), 'w') as f:
        json.dump(forecast_data, f, indent=2)

    # Save data provenance JSON
    provenance_data = {
        "framework": "ClimateTwin Spatial Flood Inundation & Impact Mapping (Phase 15)",
        "layers": {
            "Copernicus_DEM": {"type": "DERIVED_GEOSPATIAL", "source": "Copernicus DEM GLO-30", "resolution": "30m", "role": "Topographic elevation depression and slope proxy"},
            "NASA_IMERG": {"type": "OBSERVED_SATELLITE", "source": "NASA GPM IMERG V07B", "resolution": "0.1 degree (~10km)", "role": "Precipitation accumulation & acceleration"},
            "ERA5_Land_Runoff": {"type": "REANALYSIS_DERIVED", "source": "ECMWF ERA5-Land", "resolution": "0.1 degree", "role": "Surface runoff stress index"},
            "Flood_Probability": {"type": "MODEL_PREDICTED", "source": "Phase 10 Random Forest Classifier", "role": "ML current-state hazard classification"},
            "Conformal_Uncertainty": {"type": "CALIBRATED_UQ", "source": "Phase 11 Inductive Conformal Prediction", "coverage": "90% marginal coverage"},
            "Inundation_Depth_Status": {"type": "PROXY_ONLY", "status": "NOT DIRECTLY OBSERVED", "role": "Relative Inundation Severity Class (LOW, MODERATE, HIGH, SEVERE)"}
        }
    }
    with open(os.path.join(SPATIAL_DIR, 'data_provenance.json'), 'w') as f:
        json.dump(provenance_data, f, indent=2)

    # Step 3: Generate 6-Panel Evaluation Graphic
    print("\n[3/6] Rendering 6-Panel Research Evaluation Graphic...")
    fig, axes = plt.subplots(2, 3, figsize=(18, 11))
    fig.patch.set_facecolor('#0f172a')
    for ax in axes.flat:
        ax.set_facecolor('#1e293b')
        ax.tick_params(colors='#94a3b8', labelsize=9)
        ax.xaxis.label.set_color('#cbd5e1')
        ax.yaxis.label.set_color('#cbd5e1')
        ax.title.set_color('#f8fafc')
        for spine in ax.spines.values():
            spine.set_color('#334155')

    # Panel 1: Ranked Spatial Flood Impact Index (SFII)
    names = [z['name'].split('&')[0].strip() for z in zone_results]
    sfiis = [z['spatial_flood_impact_index'] for z in zone_results]
    colors = ['#ef4444' if s >= 0.75 else '#f97316' if s >= 0.55 else '#eab308' if s >= 0.35 else '#10b981' for s in sfiis]
    bars = axes[0, 0].barh(names[::-1], sfiis[::-1], color=colors[::-1], height=0.6)
    axes[0, 0].set_xlim(0, 1.1)
    axes[0, 0].set_xlabel("Spatial Flood Impact Index (SFII)")
    axes[0, 0].set_title("Panel 1: Ranked Spatial Flood Impact by Zone", fontsize=11, fontweight='bold')
    axes[0, 0].axvline(0.75, color='#ef4444', linestyle='--', alpha=0.6, label='Severe (>=0.75)')
    axes[0, 0].axvline(0.55, color='#f97316', linestyle='--', alpha=0.6, label='High (>=0.55)')
    axes[0, 0].legend(loc='lower right', facecolor='#0f172a', edgecolor='#334155', labelcolor='#cbd5e1', fontsize=8)
    for bar, val in zip(bars, sfiis[::-1]):
        axes[0, 0].text(val + 0.02, bar.get_y() + bar.get_height()/2, f"{val:.3f}", va='center', color='#f8fafc', fontweight='bold', fontsize=8)

    # Panel 2: Multi-Factor Decomposition
    x = np.arange(len(names[:4]))
    width = 0.2
    top4 = zone_results[:4]
    top_names = [z['name'].split('&')[0].strip() for z in top4]
    axes[0, 1].bar(x - 1.5*width, [0.90]*4, width, label='Rainfall (0.90)', color='#3b82f6')
    axes[0, 1].bar(x - 0.5*width, [0.75]*4, width, label='Runoff (0.75)', color='#06b6d4')
    axes[0, 1].bar(x + 0.5*width, [z['terrain_susceptibility'] for z in top4], width, label='Terrain Susc (TSS)', color='#f59e0b')
    axes[0, 1].bar(x + 1.5*width, [z['flood_susceptibility_index'] for z in top4], width, label='Flood Susc (FSI)', color='#a855f7')
    axes[0, 1].set_xticks(x)
    axes[0, 1].set_xticklabels(top_names, rotation=15, ha='right', color='#cbd5e1', fontsize=8)
    axes[0, 1].set_ylim(0, 1.1)
    axes[0, 1].set_ylabel("Factor Normalized Intensity [0, 1]")
    axes[0, 1].set_title("Panel 2: Susceptibility Factor Decomposition", fontsize=11, fontweight='bold')
    axes[0, 1].legend(facecolor='#0f172a', edgecolor='#334155', labelcolor='#cbd5e1', fontsize=8)

    # Panel 3: DEM Elevation vs Terrain Susceptibility
    all_elevs = [z['dem_elevation_m'] for z in zone_results]
    all_tss = [z['terrain_susceptibility'] for z in zone_results]
    axes[0, 2].scatter(all_elevs, all_tss, color='#38bdf8', s=100, zorder=5, edgecolor='#ffffff')
    for z in zone_results:
        axes[0, 2].annotate(z['name'].split()[0], (z['dem_elevation_m'], z['terrain_susceptibility']), textcoords="offset points", xytext=(0,7), ha='center', color='#94a3b8', fontsize=7)
    elev_curve = np.linspace(0, 45, 100)
    tss_curve = [spatial_inundation_engine.calculate_terrain_susceptibility(e, 13.01, 80.25) for e in elev_curve]
    axes[0, 2].plot(elev_curve, tss_curve, color='#f43f5e', linestyle='-', linewidth=2, label='Depression Gradient')
    axes[0, 2].set_xlabel("Copernicus DEM Elevation (m)")
    axes[0, 2].set_ylabel("Terrain Susceptibility (TSS)")
    axes[0, 2].set_title("Panel 3: DEM Elevation vs Terrain Susceptibility", fontsize=11, fontweight='bold')
    axes[0, 2].legend(facecolor='#0f172a', edgecolor='#334155', labelcolor='#cbd5e1', fontsize=8)

    # Panel 4: Multi-Horizon Forecast Progression
    horizons = ['current', '15m', '30m', '60m']
    for idx, z in enumerate(zone_results[:4]):
        vals = [z['forecast_progression'][h] for h in horizons]
        axes[1, 0].plot(['NOW', '+15m', '+30m', '+60m'], vals, marker='o', linewidth=2.5, label=z['name'].split()[0])
    axes[1, 0].set_ylim(0.4, 1.05)
    axes[1, 0].set_ylabel("Spatial Flood Impact Index (SFII)")
    axes[1, 0].set_title("Panel 4: Multi-Horizon Spatial Impact Forecast", fontsize=11, fontweight='bold')
    axes[1, 0].grid(True, color='#334155', linestyle=':', alpha=0.5)
    axes[1, 0].legend(facecolor='#0f172a', edgecolor='#334155', labelcolor='#cbd5e1', fontsize=8)

    # Panel 5: Conformal Prediction Intervals (90% Coverage)
    y_pos = np.arange(len(names))
    sfii_vals = [z['spatial_flood_impact_index'] for z in zone_results]
    lowers = [z['prediction_interval']['lower'] for z in zone_results]
    uppers = [z['prediction_interval']['upper'] for z in zone_results]
    xerr = [np.array(sfii_vals) - np.array(lowers), np.array(uppers) - np.array(sfii_vals)]
    axes[1, 1].errorbar(sfii_vals, y_pos, xerr=xerr, fmt='o', color='#38bdf8', ecolor='#a78bfa', elinewidth=2.5, capsize=4, label='90% Conformal Interval')
    axes[1, 1].set_yticks(y_pos)
    axes[1, 1].set_yticklabels(names, fontsize=8, color='#cbd5e1')
    axes[1, 1].set_xlim(0, 1.1)
    axes[1, 1].set_xlabel("SFII with 90% Prediction Interval")
    axes[1, 1].set_title("Panel 5: Spatial Conformal Uncertainty Bounds", fontsize=11, fontweight='bold')
    axes[1, 1].legend(facecolor='#0f172a', edgecolor='#334155', labelcolor='#cbd5e1', fontsize=8)

    # Panel 6: Spatial Coordinates and Inundation Severity Map
    for z in zone_results:
        c = '#ef4444' if z['relative_severity_class'] == 'SEVERE' else '#f97316' if z['relative_severity_class'] == 'HIGH' else '#eab308' if z['relative_severity_class'] == 'MODERATE' else '#10b981'
        b = z['bounds']
        rect = plt.Rectangle((b['min_lon'], b['min_lat']), b['max_lon']-b['min_lon'], b['max_lat']-b['min_lat'],
                             facecolor=c, alpha=0.35, edgecolor=c, linewidth=1.5)
        axes[1, 2].add_patch(rect)
        axes[1, 2].scatter(z['center']['lon'], z['center']['lat'], color=c, s=60, edgecolors='#ffffff')
        axes[1, 2].annotate(f"{z['name'].split()[0]}\n({z['spatial_flood_impact_index']:.2f})",
                            (z['center']['lon'], z['center']['lat']),
                            textcoords="offset points", xytext=(0,5), ha='center', color='#f8fafc', fontsize=7, fontweight='bold')

    axes[1, 2].set_xlim(79.75, 80.38)
    axes[1, 2].set_ylim(12.88, 13.32)
    axes[1, 2].set_xlabel("Longitude (°E)")
    axes[1, 2].set_ylabel("Latitude (°N)")
    axes[1, 2].set_title("Panel 6: Spatial Catchment Inundation Severity Map", fontsize=11, fontweight='bold')
    axes[1, 2].grid(True, color='#334155', linestyle=':', alpha=0.4)

    plt.tight_layout()
    plot_path = os.path.join(PLOT_DIR, 'phase15_spatial_evaluation.png')
    plt.savefig(plot_path, dpi=200, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    print(f"  -> Saved 6-panel evaluation plot to {plot_path}")

    # Step 4: Markdown Validation Report
    print("\n[4/6] Writing Spatial Validation Report...")
    report_path = os.path.join(SPATIAL_DIR, 'spatial_validation_report.md')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# ClimateTwin Phase 15 — Spatial Flood Inundation & Impact Mapping Report\n\n")
        f.write("## Executive Summary\n")
        f.write("Phase 15 connects NASA IMERG precipitation, ERA5-Land runoff, Copernicus DEM GLO-30 terrain, and Phase 10-14 machine learning & asset vulnerability into a spatially explicit **Flood Susceptibility Index (FSI)** and **Spatial Flood Impact Index (SFII)**.\n\n")
        f.write("## Monitored Spatial Catchment Zones\n\n")
        f.write(format_markdown_table(df_inv))
        f.write("\n\n## Scientific Data Provenance\n")
        f.write("- **OBSERVED**: NASA GPM IMERG V07B precipitation, CMWSSB reservoir storage.\n")
        f.write("- **SATELLITE / REANALYSIS-DERIVED**: ERA5-Land surface runoff index.\n")
        f.write("- **DERIVED**: Copernicus DEM 30m terrain susceptibility, proximity to drainage waterways.\n")
        f.write("- **MODEL-PREDICTED**: ML Random Forest flood probability & multi-horizon progression.\n")
        f.write("- **PROXY**: Relative Inundation Severity Class (LOW, MODERATE, HIGH, SEVERE). Physical water depth is NOT DIRECTLY OBSERVED.\n")
        f.write("- **RULE-BASED**: Systemic criticality and priority action policies.\n")
    print(f"  -> Saved report to {report_path}")

    # Step 5: Write spatial methodology markdown
    meth_path = os.path.join(SPATIAL_DIR, 'spatial_methodology.md')
    with open(meth_path, 'w', encoding='utf-8') as f:
        f.write("# Spatial Flood Inundation & Impact Mapping Methodology (Phase 15)\n\n")
        f.write("### Mathematical Formulations\n\n")
        f.write("1. **Terrain-Derived Flood Susceptibility ($TSS$)**:\n")
        f.write("   $$TSS = w_{\\text{elev}} \\cdot \\max(0, 1 - \\text{Elev}/25.0) + w_{\\text{channel}} \\cdot \\text{ChannelProximity} + w_{\\text{coast}} \\cdot \\text{CoastProximity} \\in [0.0, 1.0]$$\n\n")
        f.write("2. **Flood Susceptibility Index ($FSI$)**:\n")
        f.write("   $$FSI = 0.35 \\cdot S_{\\text{rain}} + 0.20 \\cdot S_{\\text{runoff}} + 0.30 \\cdot TSS + 0.15 \\cdot S_{\\text{hist}} \\in [0.0, 1.0]$$\n\n")
        f.write("3. **Spatial Flood Impact Index ($SFII$)**:\n")
        f.write("   $$SFII = P(\\text{Flood}) \\cdot 0.50 + FSI \\cdot 0.35 + \\text{CompoundBonus} \\cdot 0.15 \\in [0.0, 1.0]$$\n\n")
        f.write("4. **Relative Inundation Severity Classification**:\n")
        f.write("   - `SEVERE`: $SFII \\ge 0.75$\n")
        f.write("   - `HIGH`: $0.55 \\le SFII < 0.75$\n")
        f.write("   - `MODERATE`: $0.35 \\le SFII < 0.55$\n")
        f.write("   - `LOW`: $SFII < 0.35$\n")
    print(f"  -> Saved methodology to {meth_path}")
    print("\n=================================================================")
    print("  PHASE 15 SPATIAL EVALUATION COMPLETED SUCCESSFULLY!")
    print("=================================================================\n")

if __name__ == '__main__':
    evaluate_spatial_mapping()
