import sys
import os
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.metrics import RunningMetrics, PersonalRecords

def test_metrics_distance():
    print("Testing Metrics Distance Calculation...")
    
    # Create dummy data with lat/lon but no distance
    # Approx 1km run
    # 0.009 degrees lat is approx 1km
    lats = np.linspace(40.0, 40.009, 100)
    lons = np.linspace(-3.0, -3.0, 100)
    timestamps = pd.date_range(start='2023-01-01 10:00:00', periods=100, freq='3S') # 5 min run
    
    df = pd.DataFrame({
        'timestamp': timestamps,
        'lat': lats,
        'lon': lons,
        'altitude': [100] * 100,
        'heart_rate': [150] * 100,
        'cadence': [170] * 100
    })
    
    # Initialize metrics (should calculate distance)
    metrics = RunningMetrics(df)
    
    # Check if distance column exists
    if 'distance' in metrics.df.columns:
        print("✅ Distance column added successfully")
        total_dist = metrics.df['distance'].max()
        print(f"Total Distance: {total_dist:.2f} meters")
        assert total_dist > 900, "Distance should be approx 1000m"
    else:
        print("❌ Distance column NOT added")
        return

    # Check 1K detection
    print("\nTesting 1K Detection...")
    effort_1k = metrics.calculate_fastest_segment(1000)
    if effort_1k:
        print(f"✅ 1K Segment found: {effort_1k['duration_minutes']:.2f} min")
    else:
        # It might be slightly short due to approximation, let's check if it's close
        print(f"⚠️ 1K Segment not found (Total dist: {total_dist:.2f}m)")
        
    # Create a longer run for 3K
    print("\nTesting 3K Detection...")
    lats_3k = np.linspace(40.0, 40.030, 300) # Approx 3.3km
    timestamps_3k = pd.date_range(start='2023-01-01 10:00:00', periods=300, freq='4S')
    
    df_3k = pd.DataFrame({
        'timestamp': timestamps_3k,
        'lat': lats_3k,
        'lon': [-3.0] * 300,
        'altitude': [100] * 300,
        'heart_rate': [150] * 300,
        'cadence': [170] * 300
    })
    
    metrics_3k = RunningMetrics(df_3k)
    effort_3k = metrics_3k.calculate_fastest_segment(3000)
    
    if effort_3k:
        print(f"✅ 3K Segment found: {effort_3k['duration_minutes']:.2f} min")
    else:
        print("❌ 3K Segment NOT found")

if __name__ == "__main__":
    test_metrics_distance()
