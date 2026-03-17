"""
TruthCert Ledger System

Append-only log of all bundles. Every run writes to the ledger regardless of outcome.
Supports learning from failures and efficiency tracking.
"""

import json
import hashlib
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict
import uuid

from ..core.primitives import (
    LedgerEntry,
    TerminalState,
    GateOutcome,
    MemoryFields,
    EfficiencyMetrics,
    ExternalRefs,
)


class LedgerStorage:
    """
    Persistent storage for the ledger using SQLite.
    Append-only with no updates or deletes allowed.
    """

    def __init__(self, db_path: str = "truthcert_ledger.db"):
        self.db_path = Path(db_path)
        self._conn = None
        self._init_db()

    def close(self) -> None:
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def _init_db(self):
        """Initialize the database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ledger_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bundle_id TEXT UNIQUE NOT NULL,
                    bundle_hash TEXT NOT NULL,
                    policy_anchor_ref TEXT NOT NULL,
                    terminal_state TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    data_json TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_bundle_id ON ledger_entries(bundle_id)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_terminal_state ON ledger_entries(terminal_state)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp ON ledger_entries(timestamp)
            """)

            # Failure patterns table for learning
            conn.execute("""
                CREATE TABLE IF NOT EXISTS failure_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    signature TEXT NOT NULL,
                    count INTEGER DEFAULT 1,
                    first_seen TEXT NOT NULL,
                    last_seen TEXT NOT NULL,
                    correction_hints TEXT,
                    bundle_ids TEXT
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_failure_signature
                ON failure_patterns(signature)
            """)

            # Efficiency statistics table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS efficiency_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    total_bundles INTEGER DEFAULT 0,
                    shipped_count INTEGER DEFAULT 0,
                    rejected_count INTEGER DEFAULT 0,
                    total_tokens INTEGER DEFAULT 0,
                    total_cost_usd REAL DEFAULT 0,
                    avg_tokens_per_field REAL DEFAULT 0,
                    early_termination_count INTEGER DEFAULT 0
                )
            """)

            conn.commit()

    def append(self, entry: LedgerEntry) -> None:
        """
        Append an entry to the ledger. Append-only - no updates.
        """
        data_json = json.dumps(entry.to_dict(), default=str)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO ledger_entries
                (bundle_id, bundle_hash, policy_anchor_ref, terminal_state, timestamp, data_json)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                entry.bundle_id,
                entry.bundle_hash,
                entry.policy_anchor_ref,
                entry.terminal_state.value,
                entry.timestamp.isoformat(),
                data_json,
            ))

            # Update failure patterns if rejected
            if entry.terminal_state == TerminalState.REJECTED and entry.memory.failure_signature:
                self._update_failure_pattern(conn, entry)

            # Update efficiency stats
            self._update_efficiency_stats(conn, entry)

            conn.commit()

    def _update_failure_pattern(self, conn: sqlite3.Connection, entry: LedgerEntry) -> None:
        """Track failure patterns for learning."""
        signature = entry.memory.failure_signature
        now = datetime.utcnow().isoformat()

        # Check if pattern exists
        cursor = conn.execute(
            "SELECT id, count, bundle_ids FROM failure_patterns WHERE signature = ?",
            (signature,)
        )
        row = cursor.fetchone()

        if row:
            # Update existing pattern
            bundle_ids = json.loads(row[2] or "[]")
            bundle_ids.append(entry.bundle_id)
            conn.execute("""
                UPDATE failure_patterns
                SET count = count + 1, last_seen = ?, bundle_ids = ?
                WHERE id = ?
            """, (now, json.dumps(bundle_ids), row[0]))
        else:
            # Insert new pattern
            conn.execute("""
                INSERT INTO failure_patterns
                (signature, first_seen, last_seen, correction_hints, bundle_ids)
                VALUES (?, ?, ?, ?, ?)
            """, (
                signature,
                now,
                now,
                entry.memory.correction_hint,
                json.dumps([entry.bundle_id]),
            ))

    def _update_efficiency_stats(self, conn: sqlite3.Connection, entry: LedgerEntry) -> None:
        """Update daily efficiency statistics."""
        date = entry.timestamp.strftime("%Y-%m-%d")

        cursor = conn.execute(
            "SELECT id FROM efficiency_stats WHERE date = ?",
            (date,)
        )
        row = cursor.fetchone()

        shipped = 1 if entry.terminal_state == TerminalState.SHIPPED else 0
        rejected = 1 if entry.terminal_state == TerminalState.REJECTED else 0
        early_term = 1 if entry.efficiency.early_termination else 0

        if row:
            conn.execute("""
                UPDATE efficiency_stats SET
                    total_bundles = total_bundles + 1,
                    shipped_count = shipped_count + ?,
                    rejected_count = rejected_count + ?,
                    total_tokens = total_tokens + ?,
                    total_cost_usd = total_cost_usd + ?,
                    early_termination_count = early_termination_count + ?
                WHERE id = ?
            """, (
                shipped,
                rejected,
                entry.efficiency.total_tokens,
                entry.efficiency.estimated_cost_usd,
                early_term,
                row[0],
            ))
        else:
            conn.execute("""
                INSERT INTO efficiency_stats
                (date, total_bundles, shipped_count, rejected_count,
                 total_tokens, total_cost_usd, early_termination_count)
                VALUES (?, 1, ?, ?, ?, ?, ?)
            """, (
                date,
                shipped,
                rejected,
                entry.efficiency.total_tokens,
                entry.efficiency.estimated_cost_usd,
                early_term,
            ))

    def get_entry(self, bundle_id: str) -> Optional[LedgerEntry]:
        """Retrieve a ledger entry by bundle ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT data_json FROM ledger_entries WHERE bundle_id = ?",
                (bundle_id,)
            )
            row = cursor.fetchone()
            if row:
                return self._parse_entry(json.loads(row[0]))
        return None

    def get_entries(
        self,
        terminal_state: Optional[TerminalState] = None,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[LedgerEntry]:
        """Query ledger entries with filters."""
        query = "SELECT data_json FROM ledger_entries WHERE 1=1"
        params = []

        if terminal_state:
            query += " AND terminal_state = ?"
            params.append(terminal_state.value)

        if since:
            query += " AND timestamp >= ?"
            params.append(since.isoformat())

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            return [self._parse_entry(json.loads(row[0])) for row in cursor.fetchall()]

    def get_failure_patterns(self, min_count: int = 3) -> List[Dict[str, Any]]:
        """Get recurring failure patterns for validator discovery."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT signature, count, first_seen, last_seen, correction_hints
                FROM failure_patterns
                WHERE count >= ?
                ORDER BY count DESC
            """, (min_count,))

            return [
                {
                    "signature": row[0],
                    "count": row[1],
                    "first_seen": row[2],
                    "last_seen": row[3],
                    "correction_hints": row[4],
                }
                for row in cursor.fetchall()
            ]

    def get_efficiency_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get efficiency summary for recent period."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT
                    SUM(total_bundles) as total,
                    SUM(shipped_count) as shipped,
                    SUM(rejected_count) as rejected,
                    SUM(total_tokens) as tokens,
                    SUM(total_cost_usd) as cost,
                    SUM(early_termination_count) as early_term
                FROM efficiency_stats
                WHERE date >= date('now', ?)
            """, (f"-{days} days",))

            row = cursor.fetchone()
            if row and row[0]:
                return {
                    "total_bundles": row[0],
                    "shipped_count": row[1],
                    "rejected_count": row[2],
                    "ship_rate": row[1] / row[0] if row[0] > 0 else 0,
                    "total_tokens": row[3],
                    "total_cost_usd": row[4],
                    "avg_tokens_per_bundle": row[3] / row[0] if row[0] > 0 else 0,
                    "early_termination_rate": row[5] / row[0] if row[0] > 0 else 0,
                }

        return {"total_bundles": 0}

    def _parse_entry(self, data: Dict[str, Any]) -> LedgerEntry:
        """Parse a ledger entry from JSON data."""
        gate_outcomes = {}
        for k, v in data.get("gate_outcomes", {}).items():
            gate_outcomes[k] = GateOutcome(
                gate_id=v["gate_id"],
                passed=v["passed"],
                details=v.get("details", {}),
                failure_reason=v.get("failure_reason"),
            )

        memory_data = data.get("memory", {})
        memory = MemoryFields(
            failure_signature=memory_data.get("failure_signature"),
            source_context=memory_data.get("source_context"),
            correction_hint=memory_data.get("correction_hint"),
            embedding=memory_data.get("embedding"),
            similar_past_failures=memory_data.get("similar_past_failures", []),
        )

        efficiency_data = data.get("efficiency", {})
        efficiency = EfficiencyMetrics(
            witnesses_used=efficiency_data.get("witnesses_used", 0),
            witnesses_converged_at=efficiency_data.get("witnesses_converged_at"),
            total_tokens=efficiency_data.get("total_tokens", 0),
            estimated_cost_usd=efficiency_data.get("estimated_cost_usd", 0),
            tokens_per_extracted_field=efficiency_data.get("tokens_per_extracted_field", 0),
            early_termination=efficiency_data.get("early_termination", False),
            budget_exceeded=efficiency_data.get("budget_exceeded", False),
            heterogeneity_achieved=efficiency_data.get("heterogeneity_achieved", False),
            model_families_used=efficiency_data.get("model_families_used", []),
        )

        return LedgerEntry(
            bundle_id=data["bundle_id"],
            bundle_hash=data["bundle_hash"],
            policy_anchor_ref=data["policy_anchor_ref"],
            rerun_recipe=data.get("rerun_recipe", {}),
            gate_outcomes=gate_outcomes,
            failure_reasons=data.get("failure_reasons", []),
            terminal_state=TerminalState(data["terminal_state"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            memory=memory,
            efficiency=efficiency,
        )


class Ledger:
    """
    High-level ledger interface.
    Wraps storage and provides convenience methods.
    """

    def __init__(self, storage: Optional[LedgerStorage] = None):
        self.storage = storage or LedgerStorage()

    def record(
        self,
        bundle_id: str,
        bundle_hash: str,
        policy_anchor_ref: str,
        rerun_recipe: Dict[str, Any],
        gate_outcomes: Dict[str, GateOutcome],
        terminal_state: TerminalState,
        failure_reasons: Optional[List[str]] = None,
        memory: Optional[MemoryFields] = None,
        efficiency: Optional[EfficiencyMetrics] = None,
        external_refs: Optional[ExternalRefs] = None,
    ) -> LedgerEntry:
        """Record a bundle to the ledger."""
        entry = LedgerEntry(
            bundle_id=bundle_id,
            bundle_hash=bundle_hash,
            policy_anchor_ref=policy_anchor_ref,
            rerun_recipe=rerun_recipe,
            gate_outcomes=gate_outcomes,
            failure_reasons=failure_reasons or [],
            terminal_state=terminal_state,
            timestamp=datetime.utcnow(),
            memory=memory or MemoryFields(),
            efficiency=efficiency or EfficiencyMetrics(),
            external_refs=external_refs,
        )

        self.storage.append(entry)
        return entry

    def get(self, bundle_id: str) -> Optional[LedgerEntry]:
        """Get a ledger entry by ID."""
        return self.storage.get_entry(bundle_id)

    def query(
        self,
        terminal_state: Optional[TerminalState] = None,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[LedgerEntry]:
        """Query ledger entries."""
        return self.storage.get_entries(
            terminal_state=terminal_state,
            since=since,
            limit=limit,
        )

    def get_failure_patterns(self, min_count: int = 3) -> List[Dict[str, Any]]:
        """Get recurring failure patterns."""
        return self.storage.get_failure_patterns(min_count)

    def get_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get efficiency statistics."""
        return self.storage.get_efficiency_summary(days)

    def generate_bundle_id(self) -> str:
        """Generate a unique bundle ID."""
        return f"bundle_{uuid.uuid4().hex[:12]}"

    def compute_bundle_hash(self, content: Dict[str, Any]) -> str:
        """Compute hash of bundle content."""
        data = json.dumps(content, sort_keys=True, default=str)
        return hashlib.sha256(data.encode()).hexdigest()

    def close(self) -> None:
        """Close the ledger and release resources."""
        if hasattr(self, 'storage') and self.storage:
            self.storage.close()
