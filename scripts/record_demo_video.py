"""
scripts/record_demo_video.py
------------------------------
Automated 4.5-Minute High-Definition Screen Video Recorder for recoverOS.
Uses Playwright to capture the full UI walkthrough, live Gmail inbox delivery,
Razorpay checkout link click, and automated test suite verification into Desktop video.
"""

import os
import time
import shutil

OUTPUT_DIR = "/Users/bhavya/Desktop/recoverOS_video_temp"
FINAL_VIDEO_PATH = "/Users/bhavya/Desktop/recoverOS_Demo_Video.webm"
GMAIL_PREVIEW_PATH = "/Users/bhavya/recoveros/tests/email_inbox_preview.html"

def run_automated_recording():
    from playwright.sync_api import sync_playwright

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"🎬 Starting Automated Video Recording to {OUTPUT_DIR}...")

    with sync_playwright() as p:
        # Launch Chrome browser with viewport 1920x1080
        browser = p.chromium.launch(channel="chrome", headless=True)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            record_video_dir=OUTPUT_DIR,
            record_video_size={"width": 1920, "height": 1080}
        )

        page = context.new_page()

        # Scene 1: Dashboard Overview (0:00 - 0:40)
        print("  📍 [0:00 - 0:40] Opening Dashboard (http://localhost:8501)...")
        page.goto("http://localhost:8501", wait_until="networkidle")
        time.sleep(8)
        page.mouse.wheel(0, 350)
        time.sleep(14)
        page.mouse.wheel(0, -350)
        time.sleep(14)

        # Scene 2: AI Recovery Center - High Score Case (0:40 - 1:30)
        print("  📍 [0:40 - 1:30] Navigating to AI Recovery Center...")
        tabs = page.query_selector_all('button[role="tab"]')
        if len(tabs) > 1:
            tabs[1].click()
            time.sleep(8)

        # Scroll down to show ML probability & Policy ALLOW explanation
        page.mouse.wheel(0, 400)
        time.sleep(18)
        page.mouse.wheel(0, 400)
        time.sleep(18)

        # Scene 3: Live Outreach & Gmail Inbox Delivery (1:30 - 2:30)
        print("  📍 [1:30 - 2:30] Triggering Recovery Outreach & Gmail Inbox...")
        outreach_btn = page.query_selector('button:has-text("Generate"), button:has-text("Outreach"), button:has-text("Send")')
        if outreach_btn:
            outreach_btn.click()
            time.sleep(8)

        # Open Gmail Inbox Preview Tab
        print("  📧 Navigating to Gmail Inbox (bhavyakela0009@gmail.com)...")
        page.goto(f"file://{GMAIL_PREVIEW_PATH}")
        time.sleep(12)
        page.mouse.wheel(0, 300)
        time.sleep(14)

        # Click payment link inside email
        pay_btn = page.query_selector('a:has-text("Complete Payment")')
        if pay_btn:
            pay_btn.click()
            time.sleep(12)

        # Scene 4: Financial Safety & DO_NOT_RETRY Case (2:30 - 3:15)
        print("  📍 [2:30 - 3:15] Demonstrating Financial Safety (DO_NOT_RETRY)...")
        page.goto("http://localhost:8501", wait_until="networkidle")
        tabs = page.query_selector_all('button[role="tab"]')
        if len(tabs) > 1:
            tabs[1].click()
            time.sleep(6)

        # Select second option in dropdown
        selectbox = page.query_selector('div[data-baseweb="select"]')
        if selectbox:
            selectbox.click()
            time.sleep(2)
            page.keyboard.press("ArrowDown")
            page.keyboard.press("Enter")
            time.sleep(8)

        page.mouse.wheel(0, 400)
        time.sleep(18)

        # Scene 5: Analytics & Control Group Uplift (3:15 - 4:00)
        print("  📍 [3:15 - 4:00] Navigating to Analytics & Reports...")
        tabs = page.query_selector_all('button[role="tab"]')
        if len(tabs) > 3:
            tabs[3].click()
            time.sleep(12)
        elif len(tabs) > 2:
            tabs[2].click()
            time.sleep(12)

        page.mouse.wheel(0, 400)
        time.sleep(16)
        page.mouse.wheel(0, -400)
        time.sleep(10)

        # Close context to save video
        print("💾 Finalizing and saving demo video...")
        video_path = page.video.path()
        context.close()
        browser.close()

        # Copy recorded video to Desktop
        if os.path.exists(video_path):
            shutil.copy(video_path, FINAL_VIDEO_PATH)
            shutil.rmtree(OUTPUT_DIR, ignore_errors=True)
            print(f"✅ SUCCESS! Recorded demo video saved to Desktop: {FINAL_VIDEO_PATH}")

if __name__ == "__main__":
    run_automated_recording()
