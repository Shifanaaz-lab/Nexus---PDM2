import os
import pandas as pd
import matplotlib.pyplot as plt
from pymongo import MongoClient
from datetime import datetime

# Use non-interactive backend for headless environments
import matplotlib
matplotlib.use('Agg')

# --- Configuration ---
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
MONGODB_DB = os.getenv("MONGODB_DB", "engine_telemetry")
COLLECTION = "live_predictions"

# Thresholds
CRITICAL_THRESHOLD = 500
WARNING_THRESHOLD = 800

def generate_static_snapshot():
    print("[*] Connecting to MongoDB...")
    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DB]
    coll = db[COLLECTION]
    
    # Fetch latest fleet data
    pipeline = [
        {"$sort": {"timestamp": -1}},
        {"$group": {
            "_id": "$engine_id",
            "latest_doc": {"$first": "$$ROOT"}
        }},
        {"$replaceRoot": {"newRoot": "$latest_doc"}}
    ]
    docs = list(coll.aggregate(pipeline))
    if not docs:
        print("[-] No data found in MongoDB!")
        return
    
    df = pd.DataFrame(docs)
    
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
    fig.suptitle("Predictive Maintenance: Research Evaluation Snapshot", weight='bold')

    # --- Plot 1: Fleet RUL Trajectories (Top 5 engines from last batch) ---
    ax1 = axs[0, 0]
    # We'll just show the latest RUL for multiple engines since we don't have the full history easily in this one-off
    # Actually, we can fetch some history from MongoDB for a few engines
    target_engines = [1, 10, 25, 50, 75]
    for eid in target_engines:
        history = list(coll.find({"engine_id": eid}).sort("cycle", -1).limit(20))
        if history:
            h_df = pd.DataFrame(history)
            h_df = h_df.sort_values('cycle')
            ax1.plot(h_df['cycle'], h_df['predicted_rul'], label=f"Engine {eid:03d}", marker='.', markersize=4)
    
    ax1.axhline(y=CRITICAL_THRESHOLD, color='red', linestyle='--', alpha=0.6, label='Critical')
    ax1.set_title("RUL Degradation Trajectories")
    ax1.set_xlabel("Lifecycle (Cycles)")
    ax1.set_ylabel("Predicted RUL")
    ax1.legend(loc='upper right')
    ax1.grid(True, alpha=0.3)

    # --- Plot 2: Comparative RUL (Bar) ---
    ax2 = axs[0, 1]
    df_sorted = df.sort_values('predicted_rul', ascending=False)
    colors = ['#e74c3c' if r <= CRITICAL_THRESHOLD else ('#f1c40f' if r <= WARNING_THRESHOLD else '#2ecc71') for r in df_sorted['predicted_rul']]
    ax2.bar(range(len(df_sorted)), df_sorted['predicted_rul'], color=colors)
    ax2.set_title("Fleet-wide RUL Comparison")
    ax2.set_xlabel("Engines (Ranked)")
    ax2.set_ylabel("Predicted RUL")
    ax2.set_xticks([])

    # --- Plot 3: Distribution ---
    ax3 = axs[1, 0]
    ax3.hist(df['predicted_rul'], bins=15, color='#3498db', alpha=0.7, edgecolor='white')
    ax3.set_title("Fleet RUL Health Distribution")
    ax3.set_xlabel("RUL (Cycles)")
    ax3.set_ylabel("Units")
    ax3.grid(axis='y', alpha=0.3)

    # --- Plot 4: Statistics ---
    ax4 = axs[1, 1]
    ax4.axis('off')
    stats = [
        ("Fleet Size", f"{len(df)} Units"),
        ("Critical", f"{len(df[df['predicted_rul'] <= CRITICAL_THRESHOLD])} Units"),
        ("Mean RUL", f"{df['predicted_rul'].mean():.1f} Cycles"),
        ("Generation Time", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    ]
    y_pos = 0.8
    ax4.text(0.1, 0.9, "ANALYTICS SUMMARY", weight='bold', size=11)
    for l, v in stats:
        ax4.text(0.1, y_pos, f"{l}:", size=10, color='#555')
        ax4.text(0.5, y_pos, v, size=10, weight='bold')
        y_pos -= 0.15

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    
    # Save as both PDF and PNG
    pdf_path = "research_evaluation_snapshot.pdf"
    png_path = "research_evaluation_snapshot.png"
    plt.savefig(pdf_path, dpi=300, bbox_inches='tight')
    plt.savefig(png_path, dpi=300, bbox_inches='tight')
    print(f"[+] Saved: {pdf_path}")
    print(f"[+] Saved: {png_path}")

if __name__ == "__main__":
    generate_static_snapshot()
