"""SQLite key-value store for memory persistence."""

import sqlite3
import json
from typing import Any, Dict, List, Optional
from datetime import datetime

from ..core.config import settings


class SQLiteKVStore:
    """SQLite-based key-value store for memory data."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize the SQLite store."""
        self.db_path = db_path or settings.db_url.replace("sqlite:///", "")
        self.init_db()
    
    def init_db(self):
        """Initialize the database schema."""
        with sqlite3.connect(self.db_path) as conn:
            # Facts table for structured memory storage
            conn.execute("""
                CREATE TABLE IF NOT EXISTS facts (
                    guid TEXT,
                    key TEXT,
                    value TEXT,
                    confidence REAL,
                    source TEXT,
                    ts TEXT,
                    PRIMARY KEY (guid, key)
                )
            """)
            
            # Legacy memory store table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_store (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Legacy relationships table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_relationships (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_key TEXT NOT NULL,
                    target_key TEXT NOT NULL,
                    relationship_type TEXT NOT NULL,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (source_key) REFERENCES memory_store(key),
                    FOREIGN KEY (target_key) REFERENCES memory_store(key)
                )
            """)
            
            conn.commit()
    
    def upsert_fact(self, guid: str, key: str, value: str, confidence: float, source: str, ts: str) -> bool:
        """Upsert a fact with guid and key as composite primary key."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO facts (guid, key, value, confidence, source, ts)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (guid, key, value, confidence, source, ts))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error upserting fact {guid}:{key}: {e}")
            return False
    
    def get_facts(self, guid: str, min_conf: float = 0.6) -> List[Dict[str, Any]]:
        """Get facts for a guid with minimum confidence threshold."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT key, value, confidence, source, ts
                    FROM facts
                    WHERE guid = ? AND confidence >= ?
                    ORDER BY confidence DESC, ts DESC
                """, (guid, min_conf))
                
                facts = []
                for row in cursor.fetchall():
                    facts.append({
                        "key": row[0],
                        "value": row[1],
                        "confidence": row[2],
                        "source": row[3],
                        "ts": row[4]
                    })
                return facts
        except Exception as e:
            print(f"Error getting facts for {guid}: {e}")
            return []
    
    def delete_fact(self, guid: str, key: str) -> bool:
        """Delete a specific fact by guid and key."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("DELETE FROM facts WHERE guid = ? AND key = ?", (guid, key))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting fact {guid}:{key}: {e}")
            return False
    
    def put(self, key: str, value: Any, metadata: Optional[Dict] = None) -> bool:
        """Store a key-value pair (legacy method)."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO memory_store (key, value, metadata, updated_at)
                    VALUES (?, ?, ?, ?)
                """, (key, json.dumps(value), json.dumps(metadata or {}), datetime.now()))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error storing key {key}: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value by key (legacy method)."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT value FROM memory_store WHERE key = ?", (key,))
                row = cursor.fetchone()
                return json.loads(row[0]) if row else None
        except Exception as e:
            print(f"Error retrieving key {key}: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """Delete a key-value pair (legacy method)."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM memory_store WHERE key = ?", (key,))
                conn.execute("DELETE FROM memory_relationships WHERE source_key = ? OR target_key = ?", (key, key))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error deleting key {key}: {e}")
            return False
    
    def list_keys(self, pattern: Optional[str] = None) -> List[str]:
        """List all keys, optionally filtered by pattern (legacy method)."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if pattern:
                    cursor = conn.execute("SELECT key FROM memory_store WHERE key LIKE ?", (f"%{pattern}%",))
                else:
                    cursor = conn.execute("SELECT key FROM memory_store")
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error listing keys: {e}")
            return []
    
    def add_relationship(self, source_key: str, target_key: str, relationship_type: str, metadata: Optional[Dict] = None) -> bool:
        """Add a relationship between two keys (legacy method)."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO memory_relationships (source_key, target_key, relationship_type, metadata)
                    VALUES (?, ?, ?, ?)
                """, (source_key, target_key, relationship_type, json.dumps(metadata or {})))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error adding relationship: {e}")
            return False
    
    def get_relationships(self, key: str) -> List[Dict]:
        """Get all relationships for a key (legacy method)."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT source_key, target_key, relationship_type, metadata, created_at
                    FROM memory_relationships
                    WHERE source_key = ? OR target_key = ?
                """, (key, key))
                
                relationships = []
                for row in cursor.fetchall():
                    relationships.append({
                        "source_key": row[0],
                        "target_key": row[1],
                        "relationship_type": row[2],
                        "metadata": json.loads(row[3]) if row[3] else {},
                        "created_at": row[4]
                    })
                return relationships
        except Exception as e:
            print(f"Error getting relationships: {e}")
            return []


# Global SQLite store instance
kv_store = SQLiteKVStore()
