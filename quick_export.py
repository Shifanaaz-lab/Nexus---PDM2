import os
import pandas as pd
import matplotlib.pyplot as plt
from pymongo import MongoClient
from datetime import datetime
import matplotlib

# Use non-interactive backend
matplotlib.use('Agg')

# --- Configuration ---
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
MONGODB_DB = os.getenv("MONGODB_DB", "engine_telemetry")
COLLECTION = "live_predictions"

# Thresholds
CRITICAL_THRESHOLD = 500
WARNING_THRESHOLD = 800

def generate_quick_export():
    print("[*] Connecting to MongoDB...")
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=2000)
    db = client[MONGODB_DB]
    coll = db[COLLECTION]
    
    # 1. Fetch ALL fleet data, but just the latest per engine (optimized)
    print("[*] Fetching latest fleet status...")
    latest_docs = list(coll.find().sort("timestamp", -1).limit(400)) # Get enough to cover 100 engines
    if not latest_docs:
        print("[-] No data found!")
        return
    
    df_all = pd.DataFrame(latest_docs)
    df = df_all.drop_duplicates(subset="engine_id").head(100) # Get latest 100 engines
    
    # 2. Fetch history for a few key assets
    target_engines = [1, 10, 25, 50, 75]
    history_data = {}
    for eid in target_engines:
        history_data[eid] = list(coll.find({"engine_id": eid}).sort("timestamp", -1).limit(50))

    # Research Aesthetics
    plt.style.use('seaborn-v0_8-paper')
    plt.rcParams.update({
        "font.family": "serif",
        "axes.labelsize": 10,
        "axes.titlesize": 12,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.fontsize": 8,
        "figure.titlesize": 14,
        "figure.dpi": 300
    })

    fig, axs = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle("Predictive Maintenance: Automated Fleet Evaluation Report", weight='bold')

    # --- Plot 1: RUL Trajectories ---
    ax1 = axs[0, 0]
    for eid, docs in history_data.items():
        if docs:
            h_df = pd.DataFrame(docs).sort_values("timestamp")
            ax1.plot(h_df['cycle'], h_df['predicted_rul'], label=f"Asset {eid:03d}", alpha=0.8)
    
    ax1.axhline(y=CRITICAL_THRESHOLD, color='red', linestyle='--', alpha=0.5)
    ax1.set_title("Historical RUL Degradation (Selected Assets)")
    ax1.set_ylabel("Predicted RUL")
    ax1.legend(loc='upper right')
    ax1.grid(True, alpha=0.2)

    # --- Plot 2: Ranked Fleet health ---
    ax2 = axs[0, 1]
    df_sorted = df.sort_values('predicted_rul', ascending=False)
    colors = ['#e74c3c' if r <= CRITICAL_THRESHOLD else ('#f1c40f' if r <= WARNING_THRESHOLD else '#2ecc71') for r in df_sorted['predicted_rul']]
    ax2.bar(range(len(df_sorted)), df_sorted['predicted_rul'], color=colors)
    ax2.set_title("Global Fleet RUL Comparison (Ranked)")
    ax2.set_xticks([])

    # --- Plot 3: Distribution ---
    ax3 = axs[1, 0]
    ax3.hist(df['predicted_rul'], bins=15, color='#3498db', alpha=0.7, edgecolor='white')
    ax3.set_title("Fleet RUL Distribution Profile")
    ax3.set_xlabel("RUL (Cycles)")
    ax3.grid(axis='y', alpha=0.2)

    # --- Plot 4: Summary Table ---
    ax4 = axs[1, 1]
    ax4.axis('off')
    stats = [
        ("Total Active Fleet", f"{len(df)} Units"),
        ("Critical Threshold", f"<{CRITICAL_THRESHOLD} Cycles"),
        ("Critical Assets", f"{len(df[df['predicted_rul'] <= CRITICAL_THRESHOLD])} Units"),
        ("Mean Fleet RUL", f"{df['predicted_rul'].mean():.1f} Cycles"),
        ("Report Data Local Time", datetime.now().strftime("%H:%M:%S"))
    ]
    y_pos = 0.8
    ax4.text(0.1, 0.9, "ANALYTICAL FLEET SUMMARY", weight='bold', size=11)
    for l, v in stats:
        ax4.text(0.1, y_pos, f"{l}:", size=10, color='#444')
        ax4.text(0.5, y_pos, v, size=10, weight='bold')
        y_pos -= 0.15

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    
    out_png = "fleet_evaluation_report.png"
    out_pdf = "fleet_evaluation_report.pdf"
    plt.savefig(out_png, dpi=300, bbox_inches='tight')
    plt.savefig(out_pdf, dpi=300, bbox_inches='tight')
    print(f"DONE:{out_png}|{out_pdf}")

if __name__ == "__main__":
    generate_quick_export()
