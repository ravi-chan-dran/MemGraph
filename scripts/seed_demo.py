"""Demo data seeding script for the Bedrock-powered Graph + Memory POC."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.memory.service import memory_service
from datetime import datetime
import json


def seed_demo_data():
    """Seed the system with demo data for retirement plan sponsor."""
    print("🌱 Seeding demo data for plan_sponsor_acme...")
    
    guid = "plan_sponsor_acme"
    
    # Demo data for retirement plan sponsor
    demo_memories = [
        {
            "text": "Plan number 12345 has bi-weekly payroll processing starting in November",
            "channel": "mock-email",
            "ts": "2024-11-01T09:00:00Z"
        },
        {
            "text": "Auto-enrollment default contribution rate is 6% with automatic escalation to 10% over 2 years",
            "channel": "mock-chat",
            "ts": "2024-11-02T14:30:00Z"
        },
        {
            "text": "Mid-year true-up will be processed in July with employee communications task assigned to HR team",
            "channel": "mock-teams",
            "ts": "2024-11-03T11:15:00Z"
        },
        {
            "text": "Safe harbor match formula: 100% of first 3% plus 50% of next 2% of employee contributions",
            "channel": "mock-voice",
            "ts": "2024-11-04T16:45:00Z"
        },
        {
            "text": "Employee education sessions scheduled for December 15th covering contribution limits and vesting schedules",
            "channel": "mock-email",
            "ts": "2024-11-05T08:30:00Z"
        },
        {
            "text": "Plan administrator prefers quarterly reporting with detailed participant analytics",
            "channel": "mock-chat",
            "ts": "2024-11-06T13:20:00Z"
        },
        {
            "text": "Compliance review scheduled for Q1 2025 with focus on ADP/ACP testing requirements",
            "channel": "mock-teams",
            "ts": "2024-11-07T10:00:00Z"
        }
    ]
    
    # Process demo memories
    print("Processing demo memories...")
    for i, memory in enumerate(demo_memories):
        result = memory_service.write_memory({
            "guid": guid,
            "text": memory["text"],
            "channel": memory["channel"],
            "ts": memory["ts"]
        })
        if result["success"]:
            print(f"✅ Memory {i+1} added: {memory['text'][:50]}...")
        else:
            print(f"❌ Error adding memory {i+1}: {result['error']}")
    
    # Get final stats
    print("\n📊 Final system statistics:")
    stats_result = memory_service.get_system_stats()
    if stats_result["success"]:
        stats = stats_result["stats"]
        print(f"Total memories: {stats['retrieval']['total_memories']}")
        print(f"Graph nodes: {stats['retrieval']['graph_stats']['total_nodes']}")
        print(f"Graph relationships: {stats['retrieval']['graph_stats']['relationship_count']}")
        print(f"Vector store documents: {stats['retrieval']['vector_stats']['count']}")
    
    print("\n🎉 Demo data seeding completed!")
    print("\n🧪 A/B Test Scenarios:")
    print("1. Ask: 'What is the match formula?' (should find safe harbor info)")
    print("2. Ask: 'When is payroll processed?' (should find bi-weekly info)")
    print("3. Ask: 'What is the auto-enrollment rate?' (should find 6% info)")
    print("4. Ask: 'When are employee communications?' (should find July/December info)")
    print("5. Forget match formula, then re-ask to see difference")


if __name__ == "__main__":
    seed_demo_data()
