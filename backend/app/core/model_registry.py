import json
import time
from typing import Dict, List, Optional
import os

class ModelRegistry:
    def __init__(self, storage_path="model_registry.json"):
        self.storage_path = storage_path
        self.registry = {"versions": {}, "active_version": None, "audit_log": []}
        self.load()

    def load(self):
        if os.path.exists(self.storage_path):
            with open(self.storage_path, "r") as f:
                self.registry = json.load(f)

    def save(self):
        with open(self.storage_path, "w") as f:
            json.dump(self.registry, f, indent=4)

    def register_model(self, version: str, path: str, author: str):
        self.registry["versions"][version] = {
            "path": path,
            "author": author,
            "timestamp": time.time(),
            "status": "pending_approval"
        }
        self.save()

    def approve_model(self, version: str, approver: str):
        if version not in self.registry["versions"]:
            raise ValueError("Model version not found.")
        self.registry["versions"][version]["status"] = "approved"
        self.registry["versions"][version]["approver"] = approver
        self.registry["versions"][version]["approved_at"] = time.time()
        self.save()

    def deploy_model(self, version: str):
        if version not in self.registry["versions"]:
            raise ValueError("Model version not found.")
        if self.registry["versions"][version]["status"] != "approved":
            raise PermissionError("Cannot deploy an unapproved model.")
        
        # Track for rollback
        if self.registry["active_version"]:
            self.registry["versions"][version]["previous_version"] = self.registry["active_version"]
            
        self.registry["active_version"] = version
        self.save()

    def rollback(self):
        current = self.registry.get("active_version")
        if not current:
            raise ValueError("No active model to rollback.")
        
        prev = self.registry["versions"][current].get("previous_version")
        if not prev:
            raise ValueError("No previous version to rollback to.")
        
        self.registry["active_version"] = prev
        self.save()
        return prev

    def log_warning(self, version: str, event_id: str, action: str, details: dict):
        self.registry["audit_log"].append({
            "timestamp": time.time(),
            "version": version,
            "event_id": event_id,
            "action": action,
            "details": details
        })
        self.save()

