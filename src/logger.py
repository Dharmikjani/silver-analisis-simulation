import logging
import json
import os

_json_log_file = None

def setup_logger(output_dir='outputs'):
    """Initialize logging, allowing overriding of the output directory for testing."""
    global _json_log_file
    os.makedirs(output_dir, exist_ok=True)
    
    # Reset logging handlers to avoid appending if called multiple times in tests
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
        
    logging.basicConfig(
        filename=os.path.join(output_dir, 'simulation_events.log'), 
        level=logging.INFO, 
        format='%(message)s', 
        filemode='w'
    )
    
    if _json_log_file is not None and not _json_log_file.closed:
        _json_log_file.close()
        
    _json_log_file = open(os.path.join(output_dir, 'simulation_events.jsonl'), 'w', encoding='utf-8')

# Initialize by default to preserve backwards compatibility
setup_logger()

def log_event(category: str, event: str, **kwargs):
    """Log both human-readable text AND structured JSON for analytics."""
    logging.info(f"[{category}] {event}")
    record = {"category": category, "event": event, **kwargs}
    if _json_log_file and not _json_log_file.closed:
        _json_log_file.write(json.dumps(record) + '\n')
        _json_log_file.flush()
