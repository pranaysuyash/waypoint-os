"""
intake.federated_intelligence — Service layer for Intelligence Pool records.

Enables cross-agency risk detection and anonymized data sharing.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import hashlib
import logging

logger = logging.getLogger("federated_intel")

@dataclass
class IntelligenceIncident:
    """Anonymized incident report for the federated pool."""
    incident_type: str  # e.g., 'visa_delay', 'weather_disruption', 'payment_gateway_down'
    location: str
    severity: int  # 1-5
    details: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0

class FederatedIntelligenceService:
    """
    Manages the global intelligence pool. 
    In production, this would communicate with a central secure enclave.
    """
    
    def __init__(self):
        # In-memory mock for now
        self._pool: List[Dict[str, Any]] = []

    def report_incident(self, agency_id: str, incident: IntelligenceIncident):
        """Adds an anonymized record to the pool."""
        # Anonymize source
        source_hash = hashlib.sha256(agency_id.encode()).hexdigest()
        
        record = {
            "type": incident.incident_type,
            "location": incident.location,
            "severity": incident.severity,
            "details": incident.details,
            "confidence": incident.confidence,
            "source_hash": source_hash,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        self._pool.append(record)
        logger.info(f"Incident reported to Federated Pool: {incident.incident_type} @ {incident.location}")

    def query_risks(self, location: str) -> List[Dict[str, Any]]:
        """Queries the pool for active risks in a location."""
        # Filter for recent high-severity hits (Mocked)
        hits = [r for r in self._pool if r["location"].lower() in location.lower()]
        
        # Add a static mock for demonstration if pool is empty
        if not hits and "Singapore" in location:
            hits.append({
                "type": "visa_processing_delay",
                "severity": 3,
                "message": "Federated Intel: Global spike in Singapore Visa rejections detected."
            })
            
        return hits

# Global singleton
intelligence_service = FederatedIntelligenceService()
