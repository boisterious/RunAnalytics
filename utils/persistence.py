"""Data Persistence Module for Apex Run Analytics

Handles loading and saving run history to JSON, with support for merging new runs
and avoiding duplicates.
"""

import json
from pathlib import Path
import pandas as pd
from datetime import datetime
import numpy as np


DATA_DIR = Path(__file__).parent.parent / 'data'
HISTORY_FILE = DATA_DIR / 'runs_history.json'


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder for datetime and numpy types"""
    
    def default(self, obj):
        if isinstance(obj, (datetime, pd.Timestamp)):
            return obj.isoformat()
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if pd.isna(obj):
            return None
        return super().default(obj)


def load_runs_history() -> list:
    """Load runs from JSON file
    
    Returns:
        List of run dictionaries with processed data
    """
    if not HISTORY_FILE.exists():
        return []
    
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Convert datetime strings back to datetime objects
        for run in data:
            run['start_time'] = pd.to_datetime(run['start_time'])
            
            # Convert data DataFrame from dict
            if 'data_dict' in run:
                run['data'] = pd.DataFrame(run['data_dict'])
                # Convert timestamp column to datetime
                if 'timestamp' in run['data'].columns:
                    run['data']['timestamp'] = pd.to_datetime(run['data']['timestamp'])
                del run['data_dict']
        
        return data
    
    except Exception as e:
        print(f"Error loading runs history: {e}")
        return []


def save_runs_history(runs: list) -> bool:
    """Save runs to JSON file
    
    Args:
        runs: List of run dictionaries
        
    Returns:
        True if successful, False otherwise
    """
    try:
        DATA_DIR.mkdir(exist_ok=True)
        
        # Prepare data for serialization
        data_to_save = []
        for run in runs:
            run_copy = run.copy()
            
            # Convert DataFrame to dict
            if 'data' in run_copy and isinstance(run_copy['data'], pd.DataFrame):
                # Convert to dict with lists for each column
                run_copy['data_dict'] = {}
                for col in run_copy['data'].columns:
                    run_copy['data_dict'][col] = run_copy['data'][col].tolist()
                del run_copy['data']
            
            data_to_save.append(run_copy)
        
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, cls=DateTimeEncoder, indent=2, ensure_ascii=False)
        
        return True
    
    except Exception as e:
        print(f"Error saving runs history: {e}")
        return False


def merge_runs(existing_runs: list, new_runs: list) -> list:
    """Merge new runs with existing, avoiding duplicates
    
    Args:
        existing_runs: List of existing run dictionaries
        new_runs: List of new run dictionaries to add
        
    Returns:
        Merged list of runs, sorted by start_time (descending)
    """
    # Use filename + start_time as unique key
    existing_keys = {
        (run['filename'], run['start_time'].isoformat()) 
        for run in existing_runs
    }
    
    merged = existing_runs.copy()
    added_count = 0
    
    for new_run in new_runs:
        key = (new_run['filename'], new_run['start_time'].isoformat())
        if key not in existing_keys:
            merged.append(new_run)
            added_count += 1
    
    # Sort by start_time descending (most recent first)
    merged.sort(key=lambda x: x['start_time'], reverse=True)
    
    return merged


def clear_history() -> bool:
    """Clear all run history
    
    Returns:
        True if successful, False otherwise
    """
    try:
        if HISTORY_FILE.exists():
            HISTORY_FILE.unlink()
        return True
    except Exception as e:
        print(f"Error clearing history: {e}")
        return False


def get_history_stats() -> dict:
    """Get statistics about stored history
    
    Returns:
        Dictionary with stats (total runs, date range, file size)
    """
    if not HISTORY_FILE.exists():
        return {
            'total_runs': 0,
            'file_size_mb': 0,
            'date_range': None
        }
    
    runs = load_runs_history()
    
    stats = {
        'total_runs': len(runs),
        'file_size_mb': HISTORY_FILE.stat().st_size / (1024 * 1024)
    }
    
    if runs:
        dates = [run['start_time'] for run in runs]
        stats['date_range'] = {
            'earliest': min(dates),
            'latest': max(dates)
        }
    else:
        stats['date_range'] = None
    
    return stats
