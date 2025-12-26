"""TCX File Parser for Running Data Extraction"""

import xml.etree.ElementTree as ET
from datetime import datetime
import pandas as pd
from typing import List, Dict, Optional
import io


class TCXParser:
    """Parser for TCX (Training Center XML) files"""
    
    # XML Namespaces used in TCX files
    NS = {
        'tcx': 'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2',
        'ns3': 'http://www.garmin.com/xmlschemas/ActivityExtension/v2'
    }
    
    def __init__(self):
        self.trackpoints = []
        
    def parse_file(self, file_content) -> Optional[pd.DataFrame]:
        """
        Parse a single TCX file and extract trackpoint data
        
        Args:
            file_content: File-like object or bytes containing TCX data
            
        Returns:
            DataFrame with columns: timestamp, lat, lon, altitude, heart_rate, cadence, distance
        """
        try:
            # Handle both file objects and bytes
            if isinstance(file_content, bytes):
                tree = ET.parse(io.BytesIO(file_content))
            else:
                tree = ET.parse(file_content)
                
            root = tree.getroot()
            
            trackpoints = []
            
            # Find all trackpoints in the TCX file
            for trackpoint in root.findall('.//tcx:Trackpoint', self.NS):
                data = self._parse_trackpoint(trackpoint)
                if data:
                    trackpoints.append(data)
            
            if not trackpoints:
                return None
                
            df = pd.DataFrame(trackpoints)
            
            # Ensure timestamp is datetime
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                
            return df
            
        except Exception as e:
            print(f"Error parsing TCX file: {e}")
            return None
    
    def _parse_trackpoint(self, trackpoint) -> Optional[Dict]:
        """Extract data from a single trackpoint element"""
        data = {}
        
        # Get timestamp
        time_elem = trackpoint.find('tcx:Time', self.NS)
        if time_elem is not None:
            data['timestamp'] = time_elem.text
        else:
            return None  # Skip trackpoints without timestamp
        
        # Get position (lat/lon)
        position = trackpoint.find('tcx:Position', self.NS)
        if position is not None:
            lat = position.find('tcx:LatitudeDegrees', self.NS)
            lon = position.find('tcx:LongitudeDegrees', self.NS)
            
            if lat is not None and lon is not None:
                data['lat'] = float(lat.text)
                data['lon'] = float(lon.text)
        
        # Get altitude
        altitude = trackpoint.find('tcx:AltitudeMeters', self.NS)
        if altitude is not None:
            data['altitude'] = float(altitude.text)
        
        # Get distance
        distance = trackpoint.find('tcx:DistanceMeters', self.NS)
        if distance is not None:
            data['distance'] = float(distance.text)
        
        # Get heart rate
        hr = trackpoint.find('.//tcx:HeartRateBpm/tcx:Value', self.NS)
        if hr is not None:
            data['heart_rate'] = int(hr.text)
        
        # Get cadence (running cadence is usually in Extensions)
        # NOTE: TCX files often store cadence for one leg only, so we multiply by 2
        cadence = trackpoint.find('tcx:Cadence', self.NS)
        if cadence is not None:
            data['cadence'] = int(cadence.text) * 2  # Convert single-leg to total SPM
        else:
            # Try to find in extensions
            ext_cadence = trackpoint.find('.//ns3:RunCadence', self.NS)
            if ext_cadence is not None:
                data['cadence'] = int(ext_cadence.text) * 2  # Convert single-leg to total SPM
        
        return data if data else None
    
    def parse_multiple_files(self, files) -> List[Dict]:
        """
        Parse multiple TCX files and return metadata for each
        
        Args:
            files: List of file-like objects
            
        Returns:
            List of dictionaries containing run metadata and DataFrames
        """
        runs = []
        
        for idx, file in enumerate(files):
            df = self.parse_file(file)
            
            if df is not None and len(df) > 0:
                # Extract basic metadata
                run_data = {
                    'id': idx,
                    'filename': getattr(file, 'name', f'Run_{idx}'),
                    'start_time': df['timestamp'].min(),
                    'end_time': df['timestamp'].max(),
                    'trackpoints': len(df),
                    'data': df
                }
                runs.append(run_data)
        
        return runs


def parse_tcx_files(uploaded_files) -> List[Dict]:
    """
    Convenience function to parse TCX files from Streamlit file uploader
    
    Args:
        uploaded_files: Files from st.file_uploader
        
    Returns:
        List of run dictionaries with metadata and data
    """
    parser = TCXParser()
    return parser.parse_multiple_files(uploaded_files)
