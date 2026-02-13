import sys
import os
import shutil
import logging
from unittest.mock import MagicMock, patch

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ResilienceVerifier")

def run_test():
    logger.info(">>> PREPARING TEST ENVIRONMENT <<<")
    
    # 1. Create a dummy 'settings.py' and 'integrations.py' in the tests folder to satisfy imports
    # But verify_resilience.py is in backend/tests.
    # graph.py is in backend/src.
    # If we copy graph.py to backend/tests, and remove relative dots, it works.
    
    src_dir = os.path.join(os.path.dirname(__file__), "../src")
    tests_dir = os.path.dirname(__file__)
    
    graph_src = os.path.join(src_dir, "graph.py")
    graph_dest = os.path.join(tests_dir, "graph_test_copy.py")
    
    with open(graph_src, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Remove relative imports
    content = content.replace("from .settings import", "from settings_mock import")
    content = content.replace("from .integrations import", "from integrations_mock import")
    content = content.replace("from langgraph.", "from langgraph_mock.")
    
    with open(graph_dest, "w", encoding="utf-8") as f:
        f.write(content)
        
    # Create mocks
    with open(os.path.join(tests_dir, "settings_mock.py"), "w") as f:
        f.write("def load_settings(): pass\n")
        f.write("def checkpoint_db_path(): return ':memory:'\n")
        f.write("def data_dir(): return '.'\n")

    with open(os.path.join(tests_dir, "integrations_mock.py"), "w") as f:
        f.write("def send_email_notification(*args, **kwargs): return {'mode': 'MOCK'}\n")
        f.write("def send_whatsapp_notification(*args, **kwargs): return {'mode': 'MOCK'}\n")
        
    # Mock langgraph
    sys.modules["langgraph_mock"] = MagicMock()
    sys.modules["langgraph_mock.graph"] = MagicMock()
    sys.modules["langgraph_mock.checkpoint.sqlite"] = MagicMock()
    
    logger.info(">>> RUNNING IMPORT <<<")
    try:
        from graph_test_copy import notify_candidates
        import integrations_mock
    except Exception as e:
        logger.error(f"Import failed: {e}")
        return

    logger.info(">>> EXECUTING RESILIENCE LOGIC <<<")
    
    state = {
        "candidates": [
            {"candidate_id": "C1", "name": "Alice", "email": "alice@ex.com", "phone": "+1"},
            {"candidate_id": "C2", "name": "Bob", "email": "bob@ex.com", "phone": "+2"}
        ],
        "scheduled": [
            {"candidate_id": "C1", "name": "Alice", "slot_iso": "2024-01-01", "calendar_link": "http"},
            {"candidate_id": "C2", "name": "Bob", "slot_iso": "2024-01-01", "calendar_link": "http"}
        ]
    }
    
    # Patch the mock functions to fail specifically
    integrations_mock.send_email_notification = MagicMock(side_effect=[
        Exception("SMTP Fail"), 
        {"mode": "REAL_SMTP"}
    ])
    integrations_mock.send_whatsapp_notification = MagicMock(side_effect=[
        {"mode": "REAL_WA"},
        Exception("Twilio Fail")
    ])
    
    # Run
    result = notify_candidates(state)
    
    # Verify
    c1 = result["scheduled"][0]
    c2 = result["scheduled"][1]
    
    logger.info(f"C1 Status: Email={c1.get('email_status')}, WA={c1.get('wa_status')}")
    logger.info(f"C2 Status: Email={c2.get('email_status')}, WA={c2.get('wa_status')}")
    
    assert c1["email_status"] == "FAILED_DEGRADED"
    assert c1["wa_status"] == "REAL_WA"
    assert c2["email_status"] == "REAL_SMTP"
    assert c2["wa_status"] == "FAILED_DEGRADED"
    
    logger.info(">>> SUCCESS: Resilience Verified! <<<")
    
    # Cleanup
    os.remove(graph_dest)
    os.remove(os.path.join(tests_dir, "settings_mock.py"))
    os.remove(os.path.join(tests_dir, "integrations_mock.py"))

if __name__ == "__main__":
    run_test()
