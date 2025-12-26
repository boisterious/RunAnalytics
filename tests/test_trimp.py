import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.training_analyzer import TrainingLoadCalculator

def test_trimp_calculation():
    calculator = TrainingLoadCalculator()
    
    print("Testing TRIMP Calculation...")
    
    # Test 1: Normal values
    trimp = calculator.calculate_trimp(duration_minutes=60, avg_hr=150, max_hr=190, gender='male')
    print(f"Test 1 (Normal): {trimp:.2f} (Expected ~ > 0)")
    assert trimp > 0, "TRIMP should be positive for normal values"
    
    # Test 2: Zero duration
    trimp = calculator.calculate_trimp(duration_minutes=0, avg_hr=150, max_hr=190)
    print(f"Test 2 (Zero Duration): {trimp} (Expected 0)")
    assert trimp == 0, "TRIMP should be 0 for zero duration"
    
    # Test 3: Zero HR
    trimp = calculator.calculate_trimp(duration_minutes=60, avg_hr=0, max_hr=190)
    print(f"Test 3 (Zero HR): {trimp} (Expected 0)")
    assert trimp == 0, "TRIMP should be 0 for zero HR"
    
    # Test 4: None values
    trimp = calculator.calculate_trimp(duration_minutes=60, avg_hr=None, max_hr=190)
    print(f"Test 4 (None HR): {trimp} (Expected 0)")
    assert trimp == 0, "TRIMP should be 0 for None HR"
    
    # Test 5: Female calculation
    trimp_f = calculator.calculate_trimp(duration_minutes=60, avg_hr=150, max_hr=190, gender='female')
    print(f"Test 5 (Female): {trimp_f:.2f}")
    assert trimp_f > 0, "TRIMP should be positive for female"
    
    print("\nAll tests passed!")

if __name__ == "__main__":
    test_trimp_calculation()
