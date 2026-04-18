"""
Fraud Detection Service for TN SecureVote
Uses Isolation Forest for anomaly detection and rule-based bot detection.
"""
import uuid
from datetime import datetime
from typing import List, Dict
from collections import defaultdict


class FraudDetectionService:
    """AI-powered fraud detection for voting anomalies."""

    def __init__(self):
        self.vote_timestamps: Dict[str, List[datetime]] = defaultdict(list)
        self.ip_vote_counts: Dict[str, int] = defaultdict(int)
        self.alerts: List[Dict] = []

    def record_vote_event(
        self,
        election_id: str,
        ip_address: str,
        timestamp: datetime,
        session_duration_ms: int = 0,
    ):
        """Record a vote event for analysis."""
        self.vote_timestamps[election_id].append(timestamp)
        self.ip_vote_counts[ip_address] += 1

        # Rule-based bot detection
        self._check_rapid_voting(election_id, ip_address, timestamp)
        self._check_ip_anomaly(election_id, ip_address)
        self._check_session_anomaly(election_id, session_duration_ms)

    def _check_rapid_voting(self, election_id: str, ip_address: str, timestamp: datetime):
        """Detect unnaturally rapid voting patterns from same IP."""
        key = f"{election_id}:{ip_address}"
        recent = [
            t for t in self.vote_timestamps.get(election_id, [])
            if (timestamp - t).total_seconds() < 60
        ]
        if len(recent) > 5:
            self._create_alert(
                election_id=election_id,
                alert_type="RAPID_VOTING",
                severity="high",
                description=f"Abnormally rapid voting detected: {len(recent)} votes in 60s from same region",
            )

    def _check_ip_anomaly(self, election_id: str, ip_address: str):
        """Detect suspicious IP patterns."""
        if self.ip_vote_counts[ip_address] > 10:
            self._create_alert(
                election_id=election_id,
                alert_type="IP_ANOMALY",
                severity="medium",
                description=f"High vote count from single IP: {self.ip_vote_counts[ip_address]} votes",
            )

    def _check_session_anomaly(self, election_id: str, session_duration_ms: int):
        """Detect bot-like session durations (too fast = automated)."""
        if 0 < session_duration_ms < 3000:
            self._create_alert(
                election_id=election_id,
                alert_type="BOT_SUSPECTED",
                severity="high",
                description=f"Suspiciously fast vote session: {session_duration_ms}ms (bot-like behavior)",
            )

    def _create_alert(self, election_id: str, alert_type: str, severity: str, description: str):
        self.alerts.append({
            "alert_id": str(uuid.uuid4()),
            "alert_type": alert_type,
            "severity": severity,
            "description": description,
            "election_id": election_id,
            "timestamp": datetime.utcnow().isoformat(),
        })

    def get_alerts(self, election_id: str = None) -> List[Dict]:
        if election_id:
            return [a for a in self.alerts if a["election_id"] == election_id]
        return self.alerts

    def run_isolation_forest(self, election_id: str) -> List[Dict]:
        """
        Run Isolation Forest anomaly detection on vote timing patterns.
        Uses scikit-learn for production-grade anomaly detection.
        """
        try:
            import numpy as np
            from sklearn.ensemble import IsolationForest

            timestamps = self.vote_timestamps.get(election_id, [])
            if len(timestamps) < 10:
                return []

            # Feature engineering: inter-vote intervals
            sorted_ts = sorted(timestamps)
            intervals = []
            for i in range(1, len(sorted_ts)):
                delta = (sorted_ts[i] - sorted_ts[i - 1]).total_seconds()
                intervals.append([delta])

            if len(intervals) < 5:
                return []

            X = np.array(intervals)
            clf = IsolationForest(contamination=0.1, random_state=42)
            predictions = clf.fit_predict(X)

            anomalies = []
            for i, pred in enumerate(predictions):
                if pred == -1:
                    anomalies.append({
                        "alert_id": str(uuid.uuid4()),
                        "alert_type": "ML_ANOMALY",
                        "severity": "medium",
                        "description": f"Isolation Forest detected anomalous voting interval: {intervals[i][0]:.1f}s",
                        "election_id": election_id,
                        "timestamp": sorted_ts[i + 1].isoformat(),
                    })

            self.alerts.extend(anomalies)
            return anomalies
        except ImportError:
            return []


# Singleton
_fraud_service = None


def get_fraud_service() -> FraudDetectionService:
    global _fraud_service
    if _fraud_service is None:
        _fraud_service = FraudDetectionService()
    return _fraud_service
