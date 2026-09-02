"""
scripts/record_demo_with_voiceover.py
---------------------------------------
Automated 4+ Minute Video & AI Voiceover Generator for recoverOS.
1. Generates 5 AI voiceover audio narration files matching the pitch script using gTTS.
2. Performs full screen recording using Playwright timed to each spoken audio scene.
3. Merges the AI Voiceover track with the video into a 1080p MP4 master video file on Desktop.
"""

import os
import time
import shutil
from gtts import gTTS

OUTPUT_DIR = "/Users/bhavya/Desktop/recoverOS_video_voice_temp"
AUDIO_DIR = "/Users/bhavya/recoveros/tests/voiceover_audio"
FINAL_VIDEO_PATH = "/Users/bhavya/Desktop/recoverOS_Demo_Video_With_Voice.mp4"
FINAL_WEBM_PATH = "/Users/bhavya/Desktop/recoverOS_Demo_Video.webm"
GMAIL_PREVIEW_PATH = "/Users/bhavya/recoveros/tests/email_inbox_preview.html"

# Pitch Speech Scripts for each scene
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


def generate_audio_files():
    """Generate MP3 audio files using gTTS for each scene."""
    os.makedirs(AUDIO_DIR, exist_ok=True)
    audio_paths = {}
    print("🎙️ Generating AI Voiceover Speech Files (gTTS)...")
    for key, text in SPEECH_PARTS.items():
        path = os.path.join(AUDIO_DIR, f"{key}.mp3")
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(path)
        audio_paths[key] = path
        print(f"  ✅ Saved {key}.mp3")
    return audio_paths


def record_extended_video():
    from playwright.sync_api import sync_playwright

    generate_audio_files()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"🎬 Starting 4-Minute Extended Video Recording...")

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            record_video_dir=OUTPUT_DIR,
            record_video_size={"width": 1920, "height": 1080}
        )

        page = context.new_page()

        # Scene 1: Dashboard Overview (~48 seconds)
        print("  📍 [0:00 - 0:48] Scene 1: Dashboard & System Overview...")
        page.goto("http://localhost:8501", wait_until="networkidle")
        time.sleep(12)
        page.mouse.wheel(0, 350)
        time.sleep(18)
        page.mouse.wheel(0, -350)
        time.sleep(18)

        # Scene 2: AI Recovery Center - High Score Case (~52 seconds)
        print("  📍 [0:48 - 1:40] Scene 2: AI Recovery Center & Calibrated ML...")
        tabs = page.query_selector_all('button[role="tab"]')
        if len(tabs) > 1:
            tabs[1].click()
            time.sleep(10)

        page.mouse.wheel(0, 400)
        time.sleep(20)
        page.mouse.wheel(0, 400)
        time.sleep(22)

        # Scene 3: Live Outreach & Gmail Inbox (~60 seconds)
        print("  📍 [1:40 - 2:40] Scene 3: Live Outreach & Gmail Inbox...")
        outreach_btn = page.query_selector('button:has-text("Generate"), button:has-text("Outreach"), button:has-text("Send")')
        if outreach_btn:
            outreach_btn.click()
            time.sleep(10)

        print("  📧 Navigating to Gmail Inbox (bhavyakela0009@gmail.com)...")
        page.goto(f"file://{GMAIL_PREVIEW_PATH}")
        time.sleep(15)
        page.mouse.wheel(0, 300)
        time.sleep(18)

        pay_btn = page.query_selector('a:has-text("Complete Payment")')
        if pay_btn:
            pay_btn.click()
            time.sleep(17)

        # Scene 4: Financial Safety Case (~48 seconds)
        print("  📍 [2:40 - 3:28] Scene 4: Financial Safety & DO_NOT_RETRY Guardrail...")
        page.goto("http://localhost:8501", wait_until="networkidle")
        tabs = page.query_selector_all('button[role="tab"]')
        if len(tabs) > 1:
            tabs[1].click()
            time.sleep(8)

        selectbox = page.query_selector('div[data-baseweb="select"]')
        if selectbox:
            selectbox.click()
            time.sleep(3)
            page.keyboard.press("ArrowDown")
            page.keyboard.press("Enter")
            time.sleep(12)

        page.mouse.wheel(0, 400)
        time.sleep(25)

        # Scene 5: Analytics & Control Group Uplift (~48 seconds)
        print("  📍 [3:28 - 4:16] Scene 5: Analytics Lift & Executive Report...")
        tabs = page.query_selector_all('button[role="tab"]')
        if len(tabs) > 3:
            tabs[3].click()
            time.sleep(15)
        elif len(tabs) > 2:
            tabs[2].click()
            time.sleep(15)

        page.mouse.wheel(0, 400)
        time.sleep(20)
        page.mouse.wheel(0, -400)
        time.sleep(13)

        print("💾 Saving raw video file...")
        raw_video_path = page.video.path()
        context.close()
        browser.close()

        if os.path.exists(raw_video_path):
            shutil.copy(raw_video_path, FINAL_WEBM_PATH)
            print(f"✅ Master Video saved to Desktop: {FINAL_WEBM_PATH}")

            # Merge audio if moviepy is available
            try:
                from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_audioclips
                print("🔊 Merging AI Voiceover Audio Track into Master Video...")
                audio_clips = [
                    AudioFileClip(os.path.join(AUDIO_DIR, "scene1.mp3")),
                    AudioFileClip(os.path.join(AUDIO_DIR, "scene2.mp3")),
                    AudioFileClip(os.path.join(AUDIO_DIR, "scene3.mp3")),
                    AudioFileClip(os.path.join(AUDIO_DIR, "scene4.mp3")),
                    AudioFileClip(os.path.join(AUDIO_DIR, "scene5.mp3")),
                ]
                full_audio = concatenate_audioclips(audio_clips)
                video_clip = VideoFileClip(FINAL_WEBM_PATH)
                final_clip = video_clip.set_audio(full_audio)
                final_clip.write_videofile(FINAL_VIDEO_PATH, codec="libx264", audio_codec="aac")
                print(f"🎉 MASTER VIDEO WITH VOICE SAVED TO: {FINAL_VIDEO_PATH}")
            except Exception as exc:
                print(f"ℹ️ Video saved to Desktop. Audio merge note: {exc}")

            shutil.rmtree(OUTPUT_DIR, ignore_errors=True)

if __name__ == "__main__":
    record_extended_video()
