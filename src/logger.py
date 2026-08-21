import logging
import json

# Setup basic text logging
logging.basicConfig(filename='outputs/simulation_events.log', level=logging.INFO, format='%(message)s', filemode='w')

# Setup JSON Lines logging
_json_log_file = open('outputs/simulation_events.jsonl', 'w', encoding='utf-8')

def log_event(category: str, event: str, **kwargs):
    """Log both human-readable text AND structured JSON for analytics."""
    logging.info(f"[{category}] {event}")
    record = {"category": category, "event": event, **kwargs}
    _json_log_file.write(json.dumps(record) + '\n')
    _json_log_file.flush()
