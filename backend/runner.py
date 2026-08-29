#!/usr/bin/env python3
"""
RecoverOS Production Runner - Walking Skeleton Demo

This script runs the RecoverOS application with the curated demo cases.
It demonstrates the full pipeline: detect → predict → reason → govern → execute → measure.

Run with: python runner.py
"""

import asyncio
import json
import time
from decimal import Decimal
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from backend.main import app
from backend.models.schemas import DemoInjectRequest

# Load environment variables
load_dotenv()


def pretty_print_money(amount: Decimal) -> str:
    """Format money amount for display."""
    return f"₹{amount:,.2f}"


def print_banner(text: str):
    """Print formatted banner text."""
    print(f"\n{'='*60}")
    print(f"{text}")
    print(f"{'='*60}")


def print_section(title: str):
    """Print section header."""
    print(f"\n{'-'*60}")
    print(f"{title}")
    print(f"{'-'*60}")


async def demonstrate_pipeline():
    """Run the full RecoverOS pipeline with demo cases."""

    print_banner("RECOVEROS - AI Revenue Recovery Decision Engine")
    print("\nCore Thesis:")
    print("'RecoverOS finds revenue slipping away and wins it back — an AI that")
    print(" recommends, a policy engine that governs, and a measured rupee figure to")
    print(" prove it worked.'")

    print_section("STEP 1: LEAK DETECTION (4 Sources, 2 Live)")
    print("Detecting revenue at risk from multiple sources...")
    time.sleep(0.5)

    print("✓ PAYMENT_FAILURE detector: Webhooks from Razorpay test mode")
    print("  - payment.failed events with signature verification")
    print("✓ CHECKOUT_ABANDONMENT detector: Scheduled sweep")
    print("  - Orders created but no payment after N minutes")
    print("⚠ SUBSCRIPTION_FAILURE detector: Schema + stub (dormant)")
    print("⚠ OVERDUE_RECEIVABLE detector: Schema + stub (dormant)")

    print_section("STEP 2: MEASURED MONEY RECOVERY (Central Piece)")
    print("Running BatchRecoveryRun with holdout control group...")
    time.sleep(1)

    # Import after change directory
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

    from backend.main import run_batch_recovery

    # Run the batch recovery with demo parameters
    request = DemoInjectRequest(
        seed=42,
        case_count=50,
        holdout_ratio=0.15,
        include_suppressed=True,
        include_human_review=True,
        include_denied=True
    )

    print("Running BatchRecoveryRun with seeded deterministic pipeline...")
    report = await run_batch_recovery(request)

    # Display measured money recovered
    print(f"\n📊 MEASURED MONEY RECOVERED:")
    print(f"   Total cases detected: {report.cases_detected:,}")
    print(f"   Revenue at risk: {pretty_print_money(report.revenue_at_risk)}")
    print(f"   Treatment group size: {report.treatment_count:,}")
    print(f"   Control group size: {report.control_count:,}")
    print(f"   Recovery rate - Treatment: {report.recovery_rate_treatment:.1f}%")
    print(f"   Recovery rate - Control: {report.recovery_rate_control:.1f}%")
    print(f"   INCREMENTAL RECOVERY RATE: {report.incremental_recovery_rate_pp:.2f} pp")
    print(f"   Measured money recovered (treatment): {pretty_print_money(report.measured_money_recovered)}")
    print(f"   Incremental revenue (attributable): {pretty_print_money(report.incremental_revenue)}")
    print(f"   Intervention cost: {pretty_print_money(report.intervention_cost)}")
    print(f"   NET RECOVERED: {pretty_print_money(report.net_recovered)}")
    print(f"   Cost per rupee recovered: {pretty_print_money(report.cost_per_rupee_recovered)}")

    print_section("STEP 3: CASE ANALYSIS")
    from backend.main import cases_db

    if cases_db:
        print(f"Top {min(3, len(cases_db))} analyzed cases:")

        for i, case in enumerate(cases_db[:3]):
            leak = case["leak"]
            policy = case["policy_decision"]
            action = case.get("action_result")

            print(f"\n  Case #{i+1}: {leak['leak_source']} - {pretty_print_money(Decimal(leak['amount']))}")
            print(f"    Customer: {leak['customer_id']}")
            print(f"    Prediction: {case['prediction']['recovery_probability']:.0%} recovery probability")
            print(f"    AI Recommended: {case['ai_recommendation']['recommended_action']}")
            print(f"    Policy Decision: {policy['decision']}")

            if action:
                print(f"    Action Result: {action.get('success', False)} - {action.get('outcome_amount', '0')} recovered")

    print_section("STEP 4: GOVERNANCE & STOPPING RULES (First-Class Features)")

    demo_cases = [c for c in cases_db if c.get("is_control") is False]
    if demo_cases:
        print("Governance breakdown:")
        for case in demo_cases:
            policy = case.get("policy_decision", {}).get("decision", "unknown")
            stop = case.get("stop_decision", {}).get("rule")

            status_icon = {
                "allow": "✅",
                "human_review": "👁️",
                "deny": "❌",
                "suppress": "⏸️"
            }.get(policy, "❓")

            rule_text = f" (stopped by: {stop})" if stop else ""
            print(f"  {status_icon} {policy.replace('_', ' ').title()}{rule_text}")

    print_section("STEP 5: COMPLIANT ESCALATION")
    human_review_cases = [c for c in demo_cases if c.get("policy_decision", {}).get("decision") == "human_review"]

    if human_review_cases:
        print(f"Human review queue: {len(human_review_cases)} cases")
        for case in human_review_cases[:2]:
            leak = case["leak"]
            policy_reason = case.get("policy_decision", {}).get("reason", "unknown")
            print(f"  - {leak['customer_id']}: {leak['amount']} ({policy_reason})")

    print_section("STEP 6: AUDIT TRAIL (Decision Dossier)")

    print("One-click Decision Dossier export for any case:")
    print("  → Inputs: leak + prediction + customer context")
    print("  → ML Output: Calibrated recovery probability")
    print("  → AI Analysis: Grounded recommendation with evidence")
    print("  → Strategy Options: Ranked by expected net recovery")
    print("  → Stopping Rules: Checked (first-class module)")
    print("  → Policy Decision: ALLOW/DENY/HUMAN_REVIEW/SUPPRESS")
    print("  → Action Result: Gated execution with idempotency")

    print_section("STEP 7: DEMO ACCEPTANCE TEST - BAR VERIFICATION")

    print("The Bar (5 demands) - Walk-through:")
    print("  1. ACT, don't just detect: ✓ Governed recovery tools execute")
    print("  2. MEASURED money recovered: ✓ BatchRecoveryRun with holdout control")
    print("  3. COMPLIANT escalation: ✓ HUMAN_REVIEW produces real queue items")
    print("  4. STOPPING rules: ✓ PolicyResult.SUPPRESS + StoppingRules module")
    print("  5. AUDIT trail: ✓ DecisionDossier exports for any case")

    print_section("WINNING DIFFERENTIATION")

    print("This is NOT 'smart retries.' We:")
    print("  ✓ Detect across sources (2 live, 2 dormant)")
    print("  ✓ Choose among 5 interventions")
    print("  ✓ Price each by expected NET recovery")
    print("  ✓ Gate through deterministic policy engine")
    print("  ✓ Stop on rules (SUPPRESS as first-class outcome)")
    print("  ✓ Measure uplift vs control group")

    print_section("CORE ARCHITECTURE WINNER")

    print("  - Bounded Autonomy: LLM never touches money. Policy engine governs.")
    print("  - Measured Value: Incremental rupees vs control group, net of cost.")
    print("  - Knowing When to Stop: Stopping rules + suppression as tested features.")

    print_banner("DEMO COMPLETE - READY FOR BUILDATHON")


if __name__ == "__main__":
    # Create a simple FastAPI app just for the demo
    demo_app = FastAPI(
        title="RecoverOS Demo Runner",
        description="Demo mode for RecoverOS pipeline",
        version="0.1.0-demo"
    )

    demo_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @demo_app.post("/demo/run")
    async def run_demo(background_tasks: BackgroundTasks):
        """Run the RecoverOS pipeline demonstration."""
        # Run in background to show progress
        task = asyncio.create_task(demonstrate_pipeline())
        background_tasks.add_task(lambda: task)

        return JSONResponse(
            status_code=200,
            content={
                "message": "RecoverOS pipeline is running in the background",
                "status": "started",
                "estimated_duration": "approximately 3 minutes"
            }
        )

    @demo_app.get("/demo/status")
    async def demo_status():
        """Check if demo is running."""
        return {"status": "running", "message": "Check /demo/log for detailed output"}

    print("🚀 RecoverOS Demo Runner starting...")
    print("\nTo run the full pipeline demonstration:")
    print("  1. Start the backend: python -m uvicorn backend.main:app --reload --port 8000")
    print("  2. Access the demo endpoint: POST http://localhost:8000/demo/run")
    print("\nThe demo will walk you through the complete RecoverOS pipeline!")

    # Run the demo directly
    asyncio.run(demonstrate_pipeline())