import os
import json
import pytest
import sys

# Ensure src is in path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from logger import setup_logger, log_event

def test_log_event_serialization_and_isolation(tmp_path):
    """Test that logger writes to custom directories and formats JSON properly."""
    # 1. Isolate the logger to a temporary pytest directory
    setup_logger(output_dir=str(tmp_path))
    
    # 2. Fire some events
    log_event("TEST", "System started", v=1, ready=True)
    log_event("WARNING", "Price drop", price=25.50)
    
    # 3. Verify text log
    log_path = tmp_path / "simulation_events.log"
    assert log_path.exists()
    content = log_path.read_text()
    assert "[TEST] System started" in content
    assert "[WARNING] Price drop" in content
    
    # 4. Verify JSON lines
    jsonl_path = tmp_path / "simulation_events.jsonl"
    assert jsonl_path.exists()
    
    lines = jsonl_path.read_text().strip().split('\n')
    assert len(lines) == 2
    
    record1 = json.loads(lines[0])
    assert record1["category"] == "TEST"
    assert record1["event"] == "System started"
    assert record1["v"] == 1
    assert record1["ready"] is True
    
    record2 = json.loads(lines[1])
    assert record2["category"] == "WARNING"
    assert record2["price"] == 25.50
