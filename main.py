import os
import sys
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from groq import Groq

from core.revision_engine import generate_today_revision

# --- Load local .env file if present ---
if os.path.exists(".env"):
    with open(".env", "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

# --- 1. Fetch Motivation (Groq LLM) ---
def get_groq_motivation():
    try:
        api_key = os.environ.get("GROQ_API_KEY", "")
        if not api_key:
            return "Discipline equals freedom. Execute the plan."
        client = Groq(api_key=api_key)
        chat = client.chat.completions.create(
            messages=[{"role": "system", "content": "You are a high-performance coach. Give a short, hard-hitting, 2-sentence motivational quote about discipline and consistency."}],
            model="llama-3.1-8b-instant",
        )
        return chat.choices[0].message.content
    except Exception:
        return "Discipline equals freedom. Execute the plan."

# --- 2. Fetch Tech News ---
def get_tech_news():
    try:
        response = requests.get('https://techcrunch.com/feed/', timeout=10)
        root = ET.fromstring(response.content)
        news_html = "<ul class='list-disc pl-5 space-y-2'>"
        for item in root.findall('./channel/item')[:5]:
            title_node = item.find('title')
            link_node = item.find('link')
            title = title_node.text if title_node is not None else "News Headline"
            link = link_node.text if link_node is not None else "#"
            news_html += f"<li><a href='{link}' target='_blank' class='text-blue-400 hover:text-blue-300 transition-colors'>{title}</a></li>"
        news_html += "</ul>"
        return news_html
    except Exception:
        return "<p class='text-gray-400'>Could not fetch news today.</p>"

# --- 3. Format Dual-Pattern Revision HTML ---
def format_revision_card_html(rev):
    primary = rev.get("primary", "")
    subsidiary = rev.get("subsidiary", "")
    takeaway = rev.get("headline_takeaway", "")
    week_num = rev.get("week_number", 1)
    day_num = rev.get("day_in_week", 1)
    
    html = f"""
    <div class="mb-4">
        <div class="flex flex-wrap items-center gap-2 mb-3">
            <span class="bg-emerald-900/60 text-emerald-400 font-mono text-xs px-3 py-1 rounded-full font-bold border border-emerald-500/30">Week {week_num} · Day {day_num} of 7</span>
            <span class="bg-blue-900/60 text-blue-300 font-mono text-xs px-3 py-1 rounded-full font-bold border border-blue-500/30">{primary} &amp; {subsidiary}</span>
        </div>
        <h3 class="text-xl font-bold text-amber-400 mb-3">💡 {takeaway}</h3>
    """
    
    if rev.get("visual_trigger"):
        html += f"<p class='text-gray-300 mb-2'><strong>Visual Trigger:</strong> {rev['visual_trigger']}</p>"
    if rev.get("plain_rule"):
        html += f"<p class='text-gray-300 mb-2'><strong>Plain-English Rule:</strong> {rev['plain_rule']}</p>"
    if rev.get("worked_micro_example"):
        html += f"<p class='text-gray-400 italic mb-2'><strong>Walkthrough:</strong> {rev['worked_micro_example']}</p>"
    if rev.get("connection_bridge"):
        html += f"<p class='text-gray-300 mb-2'><strong>Connection Bridge:</strong> {rev['connection_bridge']}</p>"
    if rev.get("boundary_switch"):
        html += f"<p class='text-gray-300 mb-2'><strong>Boundary Switch:</strong> {rev['boundary_switch']}</p>"
    if rev.get("problem_statement"):
        html += f"<p class='text-gray-300 mb-1'><strong>Mixed Problem:</strong> {rev['problem_statement']}</p>"
        if rev.get("solution_sketch"):
            html += f"<p class='text-gray-400 italic mb-2'><strong>Approach:</strong> {rev['solution_sketch']}</p>"
    if rev.get("quiz_question"):
        html += f"<p class='text-gray-300 mb-1'><strong>Recall Quiz:</strong> {rev['quiz_question']}</p>"
        html += f"<p class='text-emerald-400 mb-2'><strong>Answer:</strong> {rev.get('quiz_answer', '')}</p>"
        
    html += "</div>"
    return html

# --- 4. Determine Gym Habit ---
def get_todays_workout():
    workouts = {
        "Monday": "Chest and Biceps", 
        "Tuesday": "Legs and Shoulders", 
        "Wednesday": "Back and Triceps", 
        "Thursday": "Rest Day", 
        "Friday": "Thighs and Biceps", 
        "Saturday": "Core and Forearms", 
        "Sunday": "Rest Day"
    }
    focus = workouts.get(datetime.today().strftime('%A'), "Rest Day")
    if "Rest" in focus: 
        return f"<p class='text-gray-300'><strong>{focus}</strong>. Focus on hydration, stretching, and recovery today.</p>"
    try:
        api_key = os.environ.get("GROQ_API_KEY", "")
        if not api_key:
            return f"<p class='text-gray-300'>Focus today: {focus}</p>"
        client = Groq(api_key=api_key)
        chat = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Fitness coach. Output HTML list only."}, 
                {"role": "user", "content": f"At a gym, target: {focus}. Give 5 exercises (barbells/cables/machines) with sets/reps as a <ul class='list-disc pl-5 text-gray-300 space-y-1'><li> list. No intro."}
            ],
            model="llama-3.1-8b-instant",
        )
        return chat.choices[0].message.content
    except Exception: 
        return f"<p class='text-gray-300'>Focus today: {focus}</p>"

# --- 5. Get Custom Focus Task ---
def get_custom_focus():
    try:
        with open("focus.txt", "r") as f:
            task = f.read().strip()
            return task if task else "Dominate the core habits!"
    except FileNotFoundError: 
        return "Dominate the core habits!"

# --- 6. Manage XP & Consistency Score ---
def manage_score(is_evening):
    try:
        with open("score.txt", "r") as f: 
            current_score = int(f.read().strip())
    except Exception: 
        current_score = 0
    points_earned = 0
    if is_evening:
        if os.environ.get("DSA_DONE") == "true": points_earned += 10
        if os.environ.get("GYM_DONE") == "true": points_earned += 10
        if os.environ.get("DEV_DONE") == "true": points_earned += 15
        current_score += points_earned
        with open("score.txt", "w") as f: 
            f.write(str(current_score))
    return current_score, points_earned

# --- 7. Execute Pipeline ---
def execute_pipeline(is_evening):
    quote = get_groq_motivation()
    news = get_tech_news()
    rev_data = generate_today_revision()
    revision_html = format_revision_card_html(rev_data)
    workout = get_todays_workout()
    custom_task = get_custom_focus()
    score, points = manage_score(is_evening)
    today_name = datetime.today().strftime('%A')
    
    sender_email = os.environ.get("EMAIL_USER")
    sender_password = os.environ.get("EMAIL_PASS")

    # Smart fallback URL for GitHub Pages / repository view
    default_url = "https://farhanabdulhakkim.github.io/CONSIS/"
    dashboard_url = os.environ.get("DASHBOARD_URL", "")
    if not dashboard_url or dashboard_url == "#":
        dashboard_url = default_url

    # Handle Email Dispatch
    if sender_email and sender_password:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = sender_email
        
        if is_evening:
            msg['Subject'] = f"✅ Daily Wrap-Up: +{points} XP Earned! (Total: {score} XP)"
            email_html = f"""
            <html><body style="font-family: Arial, sans-serif; background-color: #f3f4f6; padding: 30px;">
                <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; padding: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                    <h2 style="color: #111827;">End of Day Review</h2>
                    <h3 style="color: #10b981;">+{points} XP Earned! Total Consistency Score: {score} XP 🏆</h3>
                    <p style="color: #4b5563;">Your focus for tomorrow has been logged.</p>
                </div>
            </body></html>
            """
        else:
            msg['Subject'] = f"🚀 Morning Brief is Live ({score} XP)"
            email_html = f"""
            <html>
              <head>
                <style>
                  body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f3f4f6; padding: 20px; }}
                  .container {{ max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; padding: 30px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                  .header {{ text-align: center; color: #111827; border-bottom: 2px solid #e5e7eb; padding-bottom: 20px; margin-bottom: 20px; }}
                  .quote-box {{ background: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; font-style: italic; font-size: 1.05em; color: #92400e; margin: 20px 0; border-radius: 4px; }}
                  .btn {{ display: inline-block; background: #2563eb; color: #ffffff !important; text-decoration: none; padding: 12px 24px; border-radius: 8px; font-weight: bold; margin: 10px 0; }}
                  .task-box {{ background: #f9fafb; padding: 15px; border-radius: 8px; border: 1px solid #e5e7eb; margin-bottom: 15px; }}
                  h2 {{ color: #374151; margin-top: 20px; border-bottom: 2px solid #f3f4f6; padding-bottom: 6px; font-size: 1.15em; }}
                </style>
              </head>
              <body>
                <div class="container">
                  <div class="header">
                    <h1 style="margin-bottom: 10px;">Good Morning, Farhan! 🚀</h1>
                    <a href="{dashboard_url}" target="_blank" class="btn">🌐 Open Morning Command Center</a>
                  </div>
                  
                  <div class="quote-box">
                    "{quote}"
                  </div>

                  <div style="text-align: center; margin: 20px 0; padding: 15px; background: #f0fdf4; border-radius: 8px; border: 1px solid #bbf7d0;">
                    <h3 style="color: #4f46e5; margin: 0;">Total Consistency Score: {score} XP 🏆</h3>
                  </div>

                  <h2>🎯 Today's Mission</h2>
                  <div class="task-box">
                    <p style="color: #10b981; font-weight: bold; font-size: 1.1em; margin: 0;">{custom_task}</p>
                  </div>

                  <h2>⚡ Daily DSA Revision (Dual-Pattern)</h2>
                  <div class="task-box">
                    {revision_html}
                  </div>

                  <h2>💪 Gym Protocol: {today_name}</h2>
                  <div class="task-box">
                    {workout}
                  </div>

                  <h2>📰 Tech Radar</h2>
                  <div class="task-box">
                    {news}
                  </div>

                  <div style="text-align: center; margin-top: 25px; padding-top: 15px; border-top: 1px solid #e5e7eb;">
                    <a href="{dashboard_url}" target="_blank" class="btn">🌐 Launch Live Web Dashboard</a>
                  </div>
                </div>
              </body>
            </html>
            """
        msg.attach(MIMEText(email_html, 'html'))

        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            server.quit()
            print("Pipeline Execution & Email Dispatch Complete!")
        except Exception as e:
            print(f"Failed to send email: {e}")
    else:
        print("EMAIL_USER or EMAIL_PASS not set. Skipping email dispatch, but index.html & revision state generated successfully.")

if __name__ == "__main__":
    is_evening = len(sys.argv) > 1 and sys.argv[1] == "--evening"
    execute_pipeline(is_evening)
