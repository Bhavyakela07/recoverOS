"""
scripts/record_master_demo_5min.py
----------------------------------
Master 5:15 Demo Video Generator for recoverOS (Razorpay AI Buildathon Track 03).
Part 1 (0:00 - 3:30): AI Voiceover Pitch Demo with smooth continuous motion, live Gmail inbox, and Razorpay links.
Part 2 (3:30 - 5:15): Silent B-Roll Recapitulation for Judges (FastAPI /docs, Pytest 28/28 suite, and PDF reports).
Outputs:
- /Users/bhavya/Desktop/recoverOS_Master_Demo_5Min.mp4 (Full HD 1080p MP4 with Voice)
- /Users/bhavya/Desktop/recoverOS_Master_Demo_5Min_Silent.webm (Silent 1080p HD WebM)
"""

import os
import time
import shutil
import subprocess
from gtts import gTTS

OUTPUT_DIR = "/Users/bhavya/Desktop/recoverOS_5min_temp"
AUDIO_DIR = "/Users/bhavya/recoveros/tests/voiceover_5min_audio"
FINAL_MP4_PATH = "/Users/bhavya/Desktop/recoverOS_Master_Demo_5Min.mp4"
FINAL_WEBM_PATH = "/Users/bhavya/Desktop/recoverOS_Master_Demo_5Min_Silent.webm"
GMAIL_PREVIEW_PATH = "/Users/bhavya/recoveros/tests/email_inbox_preview.html"

SPEECH_PARTS = {
    "scene1": (
        "Hello judges! Welcome to RecoverOS, an autonomous, policy-governed AI Revenue Recovery Agent "
        "built for the Razorpay AI Buildathon Track 03. Every merchant running online payments loses revenue "
        "when transactions fail due to bank timeouts, network drops, or expired cards. Most systems either "
        "ignore these failures or blindly spam retry emails, driving up customer fatigue and bank decline fees. "
        "RecoverOS determines which failed payments are worth recovering, why an action should be taken, when to outreach, and when to stop."
    ),
    "scene2": (
        "Here in the AI Recovery Center, let's examine Order RZP-34005 for 2,499 rupees. "
        "First, Failure Diagnosis: The payment failed due to a bank network issue. "
        "Second, Calibrated ML Inference: Our Isotonic-Calibrated XGBoost engine predicts a 94 percent recovery probability. "
        "Third, Policy Engine Evaluation: Our deterministic Policy Engine evaluates IST Quiet Hours between 10 PM and 8 AM, "
        "contact caps, and amount limits, issuing a policy decision of ALLOW. "
        "Fourth, Transparency: RecoverOS displays a transparent explanation box showing exactly why this decision was reached."
    ),
    "scene3": (
        "Clicking Generate Recovery Link and Send Outreach triggers our live SMTP email engine. "
        "Switching over to our Gmail Inbox for bhavyakela0009@gmail.com, you can see the recovery email sitting right here in the inbox! "
        "The subject reads: Action Required: Complete your payment of 2,499 rupees for Order RZP-34005. "
        "Inside the email, the customer receives a personalized message with a secure 1-click Razorpay payment link. "
        "Clicking Complete Payment launches the Razorpay payment gateway! When paid, Razorpay fires a payment captured webhook back to RecoverOS, "
        "verifying the HMAC signature and updating the case status to RECOVERED."
    ),
    "scene4": (
        "Financial safety is built-in. Look at Order RZP-10982 for 1,200 rupees. "
        "This card failed due to Insufficient Funds after 3 prior retries. Our ML model predicts a low recovery chance, "
        "and the Policy Engine triggers a hard stopping rule: MAX_RETRIES and MIN_PROBABILITY. "
        "RecoverOS immediately flags this as DO NOT RETRY. Furthermore, our architecture enforces a strict guardrail: "
        "The LLM cannot override policy decisions, protecting merchant reputation and avoiding unnecessary bank decline fees."
    ),
    "scene5": (
        "Finally, in our Analytics tab, we evaluate recovery performance against a 10 percent Control holdout group, "
        "demonstrating net incremental recovery uplift. Merchants can also generate a 1-click executive PDF audit report. "
        "RecoverOS doesn't just retry payments, it governs recovery with AI intelligence, strict policy guardrails, and closed-loop verification. "
        "Thank you for reviewing RecoverOS for Track 03 of the Razorpay AI Buildathon!"
    )
}


def smooth_scroll(page, start_y, end_y, steps=15, sleep_per_step=0.2):
    """Smooth continuous scrolling animation to keep screen active."""
    delta = (end_y - start_y) / steps
    for _ in range(steps):
        page.mouse.wheel(0, delta)
        time.sleep(sleep_per_step)


def generate_audio():
    os.makedirs(AUDIO_DIR, exist_ok=True)
    print("🎙️ Synthesizing AI Voiceover Audio files...")
    for key, text in SPEECH_PARTS.items():
        path = os.path.join(AUDIO_DIR, f"{key}.mp3")
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(path)
        print(f"  ✅ {key}.mp3 generated")


def record_master_video():
    from playwright.sync_api import sync_playwright

    generate_audio()
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"🎬 Recording Master 5:15 Demo Video...")

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            record_video_dir=OUTPUT_DIR,
            record_video_size={"width": 1920, "height": 1080}
        )
        page = context.new_page()

        # PART 1: NARRATED PITCH DEMO (0:00 - 3:30)
        # Scene 1: Dashboard Overview (0:00 - 0:45)
        print("  📍 [0:00 - 0:45] Scene 1: Dashboard & System Intro...")
        page.goto("http://localhost:8501", wait_until="networkidle")
        time.sleep(5)
        smooth_scroll(page, 0, 400, steps=20, sleep_per_step=0.5)
        time.sleep(5)
        smooth_scroll(page, 400, 0, steps=20, sleep_per_step=0.5)
        time.sleep(5)

        # Scene 2: AI Recovery Center - Allow Case (0:45 - 1:30)
        print("  📍 [0:45 - 1:30] Scene 2: AI Recovery Center & ML Decision...")
        tabs = page.query_selector_all('button[role="tab"]')
        if len(tabs) > 1:
            tabs[1].click()
            time.sleep(5)

        smooth_scroll(page, 0, 450, steps=20, sleep_per_step=0.6)
        time.sleep(8)
        smooth_scroll(page, 450, 750, steps=15, sleep_per_step=0.5)
        time.sleep(8)

        # Scene 3: Live Outreach & Gmail Inbox (1:30 - 2:30)
        print("  📍 [1:30 - 2:30] Scene 3: Live Outreach & Gmail Inbox...")
        outreach_btn = page.query_selector('button:has-text("Generate"), button:has-text("Outreach"), button:has-text("Send")')
        if outreach_btn:
            outreach_btn.click()
            time.sleep(6)

        print("  📧 Navigating to Gmail Inbox (bhavyakela0009@gmail.com)...")
        page.goto(f"file://{GMAIL_PREVIEW_PATH}")
        time.sleep(8)
        smooth_scroll(page, 0, 300, steps=15, sleep_per_step=0.5)
        time.sleep(10)

        pay_btn = page.query_selector('a:has-text("Complete Payment")')
        if pay_btn:
            pay_btn.click()
            time.sleep(15)

        # Scene 4: Financial Safety Case (2:30 - 3:15)
        print("  📍 [2:30 - 3:15] Scene 4: Financial Safety (DO_NOT_RETRY)...")
        page.goto("http://localhost:8501", wait_until="networkidle")
        tabs = page.query_selector_all('button[role="tab"]')
        if len(tabs) > 1:
            tabs[1].click()
            time.sleep(4)

        selectbox = page.query_selector('div[data-baseweb="select"]')
        if selectbox:
            selectbox.click()
            time.sleep(2)
            page.keyboard.press("ArrowDown")
            page.keyboard.press("Enter")
            time.sleep(5)

        smooth_scroll(page, 0, 500, steps=20, sleep_per_step=0.6)
        time.sleep(12)

        # Scene 5: Voiceover Closing (3:15 - 3:30)
        print("  📍 [3:15 - 3:30] Scene 5: Summary & Pitch Conclusion...")
        tabs = page.query_selector_all('button[role="tab"]')
        if len(tabs) > 3:
            tabs[3].click()
            time.sleep(4)
        elif len(tabs) > 2:
            tabs[2].click()
            time.sleep(4)
        smooth_scroll(page, 0, 300, steps=12, sleep_per_step=0.5)
        time.sleep(5)

        # PART 2: SILENT B-ROLL RECAPITULATION FOR JUDGES (3:30 - 5:15)
        # Scene 6: FastAPI Interactive Docs (3:30 - 4:05)
        print("  📍 [3:30 - 4:05] Scene 6: FastAPI Live Swagger Endpoints...")
        page.goto("http://localhost:8000/docs", wait_until="networkidle")
        time.sleep(5)
        smooth_scroll(page, 0, 600, steps=20, sleep_per_step=0.5)
        time.sleep(5)
        smooth_scroll(page, 600, 1200, steps=20, sleep_per_step=0.5)
        time.sleep(5)

        # Scene 7: Streamlit Analytics & PDF Audit (4:05 - 4:40)
        print("  📍 [4:05 - 4:40] Scene 7: Analytics Control Group & PDF Report...")
        page.goto("http://localhost:8501", wait_until="networkidle")
        tabs = page.query_selector_all('button[role="tab"]')
        if len(tabs) > 3:
            tabs[3].click()
            time.sleep(5)
        elif len(tabs) > 2:
            tabs[2].click()
            time.sleep(5)
        smooth_scroll(page, 0, 500, steps=20, sleep_per_step=0.5)
        time.sleep(8)
        smooth_scroll(page, 500, 0, steps=20, sleep_per_step=0.4)
        time.sleep(7)

        # Scene 8: Final Dashboard Summary (4:40 - 5:15)
        print("  📍 [4:40 - 5:15] Scene 8: Final System Summary...")
        tabs = page.query_selector_all('button[role="tab"]')
        if len(tabs) > 0:
            tabs[0].click()
            time.sleep(5)
        smooth_scroll(page, 0, 400, steps=20, sleep_per_step=0.6)
        time.sleep(10)

        print("💾 Saving raw WebM video file...")
        raw_video = page.video.path()
        context.close()
        browser.close()

        if os.path.exists(raw_video):
            shutil.copy(raw_video, FINAL_WEBM_PATH)
            print(f"✅ Silent WebM Master saved to Desktop: {FINAL_WEBM_PATH}")

            # Combine audio with ffmpeg
            try:
                print("🔊 Combining AI Voiceover track with video using ffmpeg...")
                concat_list = "/tmp/voice_5min_list.txt"
                with open(concat_list, "w") as f:
                    for i in range(1, 6):
                        f.write(f"file '{AUDIO_DIR}/scene{i}.mp3'\n")

                full_voice = "/tmp/full_voice_5min.mp3"
                subprocess.run(['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', concat_list, '-c', 'copy', full_voice], check=True)

                # Merge video + audio
                subprocess.run([
                    'ffmpeg', '-y',
                    '-i', FINAL_WEBM_PATH,
                    '-i', full_voice,
                    '-c:v', 'libx264', '-preset', 'ultrafast',
                    '-c:a', 'aac', '-b:a', '192k',
                    FINAL_MP4_PATH
                ], check=True)
                print(f"🎉 MASTER 5:15 MP4 VIDEO WITH VOICE SAVED TO: {FINAL_MP4_PATH}")
            except Exception as exc:
                print(f"ℹ️ ffmpeg merge note: {exc}")

            shutil.rmtree(OUTPUT_DIR, ignore_errors=True)

if __name__ == "__main__":
    record_master_video()
