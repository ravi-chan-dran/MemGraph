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
    
    # Comprehensive demo data for retirement plan sponsor with realistic interactions
    demo_memories = [
        # Email thread: Plan setup discussion
        {
            "text": "Sarah Johnson (HR Director) to Mike Chen (Plan Administrator): We need to finalize the 401k plan setup for ACME Corp. Can we schedule a call this week to discuss the enrollment process and contribution matching?",
            "channel": "email",
            "ts": "2024-10-28T09:15:00Z",
            "thread_id": "plan_setup_2024"
        },
        {
            "text": "Mike Chen to Sarah Johnson: Absolutely! I have Tuesday at 2 PM available. I'll send over our standard plan documents and we can review the safe harbor options. The current proposal shows 100% match on first 3% plus 50% on next 2%.",
            "channel": "email", 
            "ts": "2024-10-28T14:22:00Z",
            "thread_id": "plan_setup_2024"
        },
        {
            "text": "Sarah Johnson to Mike Chen: Perfect, Tuesday works. I'll also invite David Kim from Finance to discuss budget implications. We're targeting 85% participation rate in year one.",
            "channel": "email",
            "ts": "2024-10-28T16:45:00Z", 
            "thread_id": "plan_setup_2024"
        },
        
        # Teams meeting: Plan design discussion
        {
            "text": "Teams Meeting - 401k Plan Design Discussion. Participants: Sarah Johnson, Mike Chen, David Kim. Sarah: 'We have 150 employees eligible for the plan. What's our recommended contribution structure?' Mike: 'For a company your size, I recommend 6% auto-enrollment with 2% annual escalation up to 10%. This typically achieves 80-85% participation.' David: 'What's the cost impact of the safe harbor match?' Mike: 'At 6% average contribution, you're looking at approximately $180K annually in matching costs.'",
            "channel": "teams",
            "ts": "2024-10-29T14:00:00Z",
            "thread_id": "plan_design_meeting"
        },
        {
            "text": "Teams Meeting continued - Sarah: 'We also need to consider the vesting schedule. What do you recommend?' Mike: 'For retention, I suggest 3-year cliff vesting for employer contributions. This balances retention with employee satisfaction.' David: 'That works with our retention goals. When can we launch?' Mike: 'If we finalize by November 15th, we can start payroll deductions in December for January 1st plan year.'",
            "channel": "teams",
            "ts": "2024-10-29T14:25:00Z",
            "thread_id": "plan_design_meeting"
        },
        
        # Slack conversation: Implementation details
        {
            "text": "Sarah Johnson in #hr-401k: 'Team, we're moving forward with the 401k plan. Mike will be sending implementation timeline tomorrow. Key dates: Nov 15 - plan documents signed, Dec 1 - employee communications begin, Jan 1 - first payroll deductions.'",
            "channel": "slack",
            "ts": "2024-10-30T10:30:00Z",
            "thread_id": "implementation_plan"
        },
        {
            "text": "David Kim in #hr-401k: 'Sarah, I've updated the budget forecast. The matching costs are built in for Q1. Should we also budget for the annual compliance testing?'",
            "channel": "slack", 
            "ts": "2024-10-30T11:15:00Z",
            "thread_id": "implementation_plan"
        },
        {
            "text": "Sarah Johnson in #hr-401k: 'Yes, Mike mentioned $5K annually for ADP/ACP testing. I'll add that to the budget. Also, we need to schedule employee education sessions for December.'",
            "channel": "slack",
            "ts": "2024-10-30T11:45:00Z",
            "thread_id": "implementation_plan"
        },
        
        # Phone call: Compliance discussion
        {
            "text": "Phone call with Mike Chen: 'Sarah, I wanted to follow up on the compliance requirements. Since you're implementing mid-year, we need to ensure the plan passes ADP/ACP testing. The safe harbor match helps, but we should also consider a QNEC if needed. Also, don't forget the 5500 filing deadline is July 31st.'",
            "channel": "phone",
            "ts": "2024-11-01T15:30:00Z",
            "thread_id": "compliance_call"
        },
        
        # Email: Plan document execution
        {
            "text": "Mike Chen to Sarah Johnson: 'The plan documents are ready for signature. I've attached the adoption agreement and summary plan description. Please review pages 12-15 for the contribution limits and vesting schedule. Once signed, I'll submit to the DOL for approval.'",
            "channel": "email",
            "ts": "2024-11-05T09:00:00Z",
            "thread_id": "plan_documents"
        },
        {
            "text": "Sarah Johnson to Mike Chen: 'Documents look good. I've signed and sent them back. When should we expect DOL approval? Also, can you send the employee communication templates?'",
            "channel": "email",
            "ts": "2024-11-05T14:20:00Z",
            "thread_id": "plan_documents"
        },
        
        # Teams meeting: Employee education planning
        {
            "text": "Teams Meeting - Employee Education Planning. Sarah: 'We have 150 employees to educate. What's the best approach?' Mike: 'I recommend 3 sessions: 30-minute overview for all, 1-hour detailed session for interested employees, and 1-on-1 meetings for high earners. We can do virtual or in-person.' Sarah: 'Let's do virtual for the overview, in-person for detailed sessions. Schedule for December 10th, 12th, and 15th.'",
            "channel": "teams",
            "ts": "2024-11-08T10:00:00Z",
            "thread_id": "education_planning"
        },
        
        # Slack: Payroll integration
        {
            "text": "David Kim in #payroll-401k: 'IT team, we need to integrate 401k deductions into the payroll system. The plan starts January 1st with bi-weekly processing. Can we have a test run in December?'",
            "channel": "slack",
            "ts": "2024-11-12T13:30:00Z",
            "thread_id": "payroll_integration"
        },
        {
            "text": "Alex Rodriguez (IT) in #payroll-401k: 'David, we can set up a test environment. What's the deduction structure? 6% default with employer match?' David: 'Yes, 6% employee contribution, employer matches 100% of first 3% plus 50% of next 2%.'",
            "channel": "slack",
            "ts": "2024-11-12T14:15:00Z",
            "thread_id": "payroll_integration"
        },
        
        # Email: DOL approval confirmation
        {
            "text": "Mike Chen to Sarah Johnson: 'Great news! DOL has approved the plan effective January 1st, 2025. The plan number is 12345. I've updated the participant portal and you can begin employee communications. The first payroll deduction will be January 15th.'",
            "channel": "email",
            "ts": "2024-11-15T11:00:00Z",
            "thread_id": "dol_approval"
        },
        
        # Teams meeting: Employee communication launch
        {
            "text": "Teams Meeting - Communication Launch. Sarah: 'The plan is approved! We're launching employee communications today. Mike, what's the key message?' Mike: 'Focus on the 6% auto-enrollment, employer matching, and the December education sessions. Emphasize that employees can opt out if they prefer.' Sarah: 'Perfect. I'll send the all-hands email this afternoon.'",
            "channel": "teams",
            "ts": "2024-11-15T14:00:00Z",
            "thread_id": "communication_launch"
        },
        
        # Email: All-hands announcement
        {
            "text": "Sarah Johnson to All Employees: 'Exciting news! ACME Corp is launching a 401k retirement plan starting January 1st, 2025. You'll be automatically enrolled at 6% of your salary with employer matching. Education sessions are scheduled for December 10th, 12th, and 15th. Please RSVP for your preferred session. Questions? Contact me or visit the employee portal.'",
            "channel": "email",
            "ts": "2024-11-15T16:00:00Z",
            "thread_id": "employee_announcement"
        },
        
        # Slack: Employee questions
        {
            "text": "Jennifer Martinez in #hr-questions: 'Sarah, I have a question about the 401k. Can I contribute more than 6%?' Sarah: 'Yes! You can contribute up to $23,000 annually (2025 limit). The 6% is just the auto-enrollment default. You can change your contribution anytime in the portal.'",
            "channel": "slack",
            "ts": "2024-11-18T09:30:00Z",
            "thread_id": "employee_questions"
        },
        {
            "text": "Robert Wilson in #hr-questions: 'What happens to the employer match if I leave before 3 years?' Sarah: 'The employer match vests over 3 years. If you leave before 3 years, you keep your contributions plus any vested employer match. After 3 years, you're 100% vested in all employer contributions.'",
            "channel": "slack",
            "ts": "2024-11-18T10:15:00Z",
            "thread_id": "employee_questions"
        },
        
        # Phone call: Education session preparation
        {
            "text": "Phone call with Mike Chen: 'Sarah, I've prepared the education materials. The presentation covers contribution limits, employer matching, investment options, and vesting. I'll also bring sample statements showing projected growth. Should we include information about Roth 401k options?'",
            "channel": "phone",
            "ts": "2024-12-05T16:00:00Z",
            "thread_id": "education_prep"
        },
        
        # Teams meeting: Education session feedback
        {
            "text": "Teams Meeting - Post-Education Session Review. Sarah: 'The sessions went well! 89% attendance rate. What were the main questions?' Mike: 'Most questions were about investment options and contribution changes. A few asked about Roth vs traditional. I think we should add a FAQ document.' Sarah: 'Good idea. Also, we had 12 employees opt out. That's 8% opt-out rate, which is normal.'",
            "channel": "teams",
            "ts": "2024-12-16T10:00:00Z",
            "thread_id": "education_review"
        },
        
        # Email: First payroll processing
        {
            "text": "David Kim to Sarah Johnson: 'First 401k payroll processed successfully! 138 employees enrolled (92% participation rate). Total employee contributions: $18,450, employer match: $9,225. Everything looks good for the January 15th pay period.'",
            "channel": "email",
            "ts": "2025-01-16T08:30:00Z",
            "thread_id": "first_payroll"
        },
        
        # Slack: Ongoing plan management
        {
            "text": "Sarah Johnson in #hr-401k: 'Team, the 401k plan is running smoothly. Participation is at 92% which exceeds our 85% target. Mike will provide quarterly reports starting in April. Any issues to address?'",
            "channel": "slack",
            "ts": "2025-01-20T14:00:00Z",
            "thread_id": "plan_management"
        },
        {
            "text": "Mike Chen in #hr-401k: 'Sarah, the plan is performing well. I'll send the Q1 report in April. Also, don't forget we need to prepare for the mid-year true-up in July. I'll send a reminder closer to that date.'",
            "channel": "slack",
            "ts": "2025-01-20T14:30:00Z",
            "thread_id": "plan_management"
        }
    ]
    
    # Process demo memories
    print("Processing demo memories...")
    for i, memory in enumerate(demo_memories):
        result = memory_service.write_memory({
            "guid": guid,
            "text": memory["text"],
            "channel": memory["channel"],
            "ts": memory["ts"],
            "thread_id": memory.get("thread_id")
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
    print("1. Ask: 'What is the employer match formula?' (should find safe harbor: 100% of first 3% plus 50% of next 2%)")
    print("2. Ask: 'When is payroll processed?' (should find bi-weekly processing starting January 15th)")
    print("3. Ask: 'What is the auto-enrollment rate?' (should find 6% with 2% annual escalation)")
    print("4. Ask: 'When are employee education sessions?' (should find December 10th, 12th, 15th)")
    print("5. Ask: 'Who are the key people involved?' (should find Sarah Johnson, Mike Chen, David Kim)")
    print("6. Ask: 'What is the participation rate?' (should find 92% actual vs 85% target)")
    print("7. Ask: 'What are the compliance requirements?' (should find ADP/ACP testing, 5500 filing)")
    print("8. Ask: 'What is the vesting schedule?' (should find 3-year cliff vesting)")
    print("9. Ask: 'What is the plan number?' (should find 12345)")
    print("10. Ask: 'What are the contribution limits?' (should find $23,000 annual limit)")
    print("11. Forget match formula, then re-ask to see difference")
    print("12. Ask: 'Show me the conversation about budget planning' (should find thread about matching costs)")
    print("13. Ask: 'What questions did employees ask?' (should find questions about contribution limits and vesting)")
    print("14. Ask: 'When was the plan approved?' (should find November 15th DOL approval)")
    print("15. Ask: 'What is the total cost of the plan?' (should find $180K annually in matching costs)")


if __name__ == "__main__":
    seed_demo_data()
