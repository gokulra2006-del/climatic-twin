import unittest
import os
import time
from backend.app.core.model_registry import ModelRegistry

class TestModelGovernance(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_registry.json"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.registry = ModelRegistry(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_registration_and_approval(self):
        self.registry.register_model("v1.0", "/models/v1.pkl", "data_team")
        self.assertEqual(self.registry.registry["versions"]["v1.0"]["status"], "pending_approval")
        
        self.registry.approve_model("v1.0", "lead_engineer")
        self.assertEqual(self.registry.registry["versions"]["v1.0"]["status"], "approved")

    def test_deploy_and_rollback(self):
        # Setup v1
        self.registry.register_model("v1.0", "path1", "auth1")
        self.registry.approve_model("v1.0", "appr1")
        self.registry.deploy_model("v1.0")
        
        # Setup v2
        self.registry.register_model("v2.0", "path2", "auth2")
        self.registry.approve_model("v2.0", "appr2")
        self.registry.deploy_model("v2.0")
        
        self.assertEqual(self.registry.registry["active_version"], "v2.0")
        
        # Rollback
        rolled_back_to = self.registry.rollback()
        self.assertEqual(rolled_back_to, "v1.0")
        self.assertEqual(self.registry.registry["active_version"], "v1.0")

    def test_unapproved_deploy_fails(self):
        self.registry.register_model("v3.0", "path3", "auth3")
        with self.assertRaises(PermissionError):
            self.registry.deploy_model("v3.0")

    def test_audit_logging(self):
        self.registry.log_warning("v1.0", "EVT_001", "deploy_pump", {"confidence": 0.95})
        log = self.registry.registry["audit_log"]
        self.assertEqual(len(log), 1)
        self.assertEqual(log[0]["event_id"], "EVT_001")
        self.assertEqual(log[0]["details"]["confidence"], 0.95)

if __name__ == "__main__":
    unittest.main()
