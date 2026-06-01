import os
import time
import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from pymongo import MongoClient
from datetime import datetime

# --- Configuration ---
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
MONGODB_DB = os.getenv("MONGODB_DB", "engine_telemetry")
COLLECTION = "live_predictions"

# Research Aesthetics
plt.style.use('seaborn-v0_8-paper')  # Professional, thin lines
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif"],
    "axes.labelsize": 10,
    "axes.titlesize": 12,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 8,
    "figure.titlesize": 14,
    "figure.dpi": 150
})

# Thresholds (Matching operational logic)
CRITICAL_THRESHOLD = 500
WARNING_THRESHOLD = 800

class ResearchPlotter:
    def __init__(self):
        self.client = MongoClient(MONGODB_URI)
        self.db = self.client[MONGODB_DB]
        self.coll = self.db[COLLECTION]
        
        # History for trajectories (caching 5 engines)
        self.target_engines = [1, 10, 25, 50, 75]
        self.history = {eid: [] for eid in self.target_engines}
        
    def get_latest_fleet_data(self):
        """Fetch latest predictions for all engines from MongoDB."""
        pipeline = [
            {"$sort": {"timestamp": -1}},
            {"$group": {
                "_id": "$engine_id",
                "latest_doc": {"$first": "$$ROOT"}
            }},
            {"$replaceRoot": {"newRoot": "$latest_doc"}}
        ]
        docs = list(self.coll.aggregate(pipeline))
        return pd.DataFrame(docs)

    def update_trajectories(self, df):
        """Cache history for specific engines for the trend plot."""
        for eid in self.target_engines:
            match = df[df['engine_id'] == eid]
            if not match.empty:
                # Add (cycle, predicted_rul)
                row = match.iloc[0]
                # Avoid duplicates
                if not self.history[eid] or self.history[eid][-1][0] < row['cycle']:
                    self.history[eid].append((row['cycle'], row['predicted_rul']))
                    # Limit history to last 50 cycles
                    if len(self.history[eid]) > 50:
                        self.history[eid].pop(0)

    def on_press(self, event):
        """Keyboard event listener for snapshots."""
        if event.key == 's':
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"research_evaluation_{timestamp}.pdf"
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            print(f"[*] Snapshot saved: {filename}")

def animate(i, plotter, axs):
    try:
        df = plotter.get_latest_fleet_data()
        if df.empty:
            return
        
        plotter.update_trajectories(df)
        
        # Clear previous artists
        for ax in axs.flatten():
            ax.clear()

        # --- Plot 1: Fleet RUL Trajectories ---
        ax1 = axs[0, 0]
        for eid, data in plotter.history.items():
            if data:
                cycles, ruls = zip(*data)
                ax1.plot(cycles, ruls, label=f"Engine {eid:03d}", marker='.', markersize=3)
        
        ax1.axhline(y=CRITICAL_THRESHOLD, color='red', linestyle='--', alpha=0.6, label='Critical Failure Area')
        ax1.set_title("RUL Degradation Trajectories (Selected Fleet Assets)")
        ax1.set_xlabel("Operational Lifecycle (Cycles)")
        ax1.set_ylabel("Predicted RUL")
        ax1.legend(loc='upper right', frameon=True, facecolor='white')
        ax1.grid(True, alpha=0.3)

        # --- Plot 2: Predictive Comparison (Ranked Bar Chart) ---
        ax2 = axs[0, 1]
        df_sorted = df.sort_values('predicted_rul', ascending=False)
        
        # Color by thresholds
        colors = []
        for rul in df_sorted['predicted_rul']:
            if rul <= CRITICAL_THRESHOLD: colors.append('#e74c3c') # Red
            elif rul <= WARNING_THRESHOLD: colors.append('#f1c40f') # Yellow
            else: colors.append('#2ecc71') # Green
        
        bars = ax2.bar(range(len(df_sorted)), df_sorted['predicted_rul'], color=colors, width=0.8)
        ax2.set_title("Fleet-wide Comparative RUL Assessment")
        ax2.set_xlabel("Engines (Ranked by Health)")
        ax2.set_ylabel("Current Predicted RUL")
        ax2.set_xticks([]) # Hide x-labels as there are too many
        
        # Custom legend for bar colors
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='#2ecc71', label='Healthy'),
            Patch(facecolor='#f1c40f', label='Warning'),
            Patch(facecolor='#e74c3c', label='Critical Risk')
        ]
        ax2.legend(handles=legend_elements, loc='upper right')

        # --- Plot 3: Fleet Health Distribution ---
        ax3 = axs[1, 0]
        n, bins, patches = ax3.hist(df['predicted_rul'], bins=20, color='#3498db', alpha=0.7, edgecolor='white')
        ax3.set_title("Predictive RUL Distribution (Fleet Overview)")
        ax3.set_xlabel("RUL Projection (Cycles)")
        ax3.set_ylabel("Engine Count")
        ax3.grid(axis='y', alpha=0.3)

        # --- Plot 4: Stats Summary (Table-like) ---
        ax4 = axs[1, 1]
        ax4.axis('off')
        stats = [
            ("Total Fleet Size", f"{len(df)} Units"),
            ("Critical Assets", f"{len(df[df['predicted_rul'] <= CRITICAL_THRESHOLD])} Units"),
            ("Warning Alerts", f"{len(df[(df['predicted_rul'] > CRITICAL_THRESHOLD) & (df['predicted_rul'] <= WARNING_THRESHOLD)])} Units"),
            ("Mean Fleet RUL", f"{df['predicted_rul'].mean():.1f} Cycles"),
            ("Min RUL Observed", f"{df['predicted_rul'].min():.1f} Cycles"),
            ("Last Data Sync", datetime.now().strftime("%H:%M:%S"))
        ]
        
        # Draw tech-style stats "paper"
        y_pos = 0.85
        ax4.text(0.05, 0.95, "SYSTEM PERFORMANCE METRICS", weight='bold', size=11)
        for label, val in stats:
            ax4.text(0.05, y_pos, label, size=10, color='#555')
            ax4.text(0.60, y_pos, val, size=10, weight='bold')
            y_pos -= 0.12
            
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        
    except Exception as e:
        print(f"[!] Error in animation: {e}")

def main():
    print("="*60)
    print(" RESEARCH EVALUATION PLOTTER - REAL-TIME SYSTEM")
    print("="*60)
    print("[*] Connecting to MongoDB...")
    
    plotter = ResearchPlotter()
    fig, axs = plt.subplots(2, 2, figsize=(12, 8))
    fig.canvas.manager.set_window_title("Predictive Maintenance - Research Evaluation")
    fig.suptitle("Predictive Maintenance System: Fleet Evaluation Report Snapshot", weight='bold')

    # Connect keyboard listener
    fig.canvas.mpl_connect('key_press_event', plotter.on_press)
    print("[+] Live plotting active. Press 's' to save high-res PDF snapshot.")

    ani = FuncAnimation(fig, animate, fargs=(plotter, axs), interval=2000, cache_frame_data=False)
    plt.show()

if __name__ == "__main__":
    main()
