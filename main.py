import os
import sys
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from groq import Groq

# [Keep functions 1 through 6 exactly the same: get_groq_motivation(), get_tech_news(), get_dsa_pattern(), get_todays_workout(), get_custom_focus(), manage_score()]

def get_groq_motivation():
    try:
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        chat = client.chat.completions.create(
            messages=[{"role": "system", "content": "You are a high-performance coach. Give a short, hard-hitting, 2-sentence motivational quote about discipline."}],
            model="llama-3.1-8b-instant",
        )
        return chat.choices[0].message.content
    except Exception: return "Discipline equals freedom. Execute the plan."

def get_tech_news():
    try:
        response = requests.get('https://techcrunch.com/feed/')
        root = ET.fromstring(response.content)
        news_html = "<ul class='list-disc pl-5 space-y-2'>"
        for item in root.findall('./channel/item')[:5]:
            title = item.find('title').text
            link = item.find('link').text
            news_html += f"<li><a href='{link}' target='_blank' class='text-blue-400 hover:text-blue-300 transition-colors'>{title}</a></li>"
        news_html += "</ul>"
        return news_html
    except Exception: return "<p>Could not fetch news today.</p>"

def get_dsa_pattern():
    patterns = {"Monday": "Graph Traversals (DFS & BFS)", "Tuesday": "Advanced Graphs", "Wednesday": "Backtracking", "Thursday": "1D Dynamic Programming", "Friday": "2D Dynamic Programming", "Saturday": "Union Find", "Sunday": "Greedy & Bit Manipulation"}
    pattern = patterns.get(datetime.today().strftime('%A'), "General Review")
    try:
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        chat = client.chat.completions.create(
            messages=[{"role": "system", "content": "You are an interviewer. Given a DSA pattern, suggest ONE classic LeetCode problem and a 1-sentence tip. Output ONLY HTML: <p class='text-xl text-white'>[Name]</p><p class='text-gray-400'>[Tip]</p>"}],
            model="llama-3.1-8b-instant",
        )
        return f"<h3 class='text-2xl font-bold text-blue-500 mb-2'>{pattern}</h3>{chat.choices[0].message.content}"
    except Exception: return f"<h3 class='text-2xl font-bold text-blue-500 mb-2'>{pattern}</h3>"

def get_todays_workout():
    workouts = {"Monday": "Chest and Biceps", "Tuesday": "Legs and Shoulders", "Wednesday": "Back and Triceps", "Thursday": "Rest Day", "Friday": "Thighs and Biceps", "Saturday": "Core and Forearms", "Sunday": "Rest Day"}
    focus = workouts.get(datetime.today().strftime('%A'), "Rest Day")
    if "Rest" in focus: return f"<p class='text-gray-300'><strong>{focus}</strong>. Focus on hydration and recovery.</p>"
    try:
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        chat = client.chat.completions.create(
            messages=[{"role": "system", "content": "Fitness coach. Output HTML list only."}, {"role": "user", "content": f"At a gym, target: {focus}. Give 5 exercises (barbells/cables/machines) with sets/reps as a <ul class='list-disc pl-5 text-gray-300 space-y-1'><li> list. No intro."}],
            model="llama-3.1-8b-instant",
        )
        return chat.choices[0].message.content
    except Exception: return f"<p class='text-gray-300'>Focus today: {focus}</p>"

def get_custom_focus():
    try:
        with open("focus.txt", "r") as f:
            task = f.read().strip()
            return task if task else "Dominate the core habits!"
    except FileNotFoundError: return "Dominate the core habits!"

def manage_score(is_evening):
    try:
        with open("score.txt", "r") as f: current_score = int(f.read().strip())
    except: current_score = 0
    points_earned = 0
    if is_evening:
        if os.environ.get("DSA_DONE") == "true": points_earned += 10
        if os.environ.get("GYM_DONE") == "true": points_earned += 10
        if os.environ.get("DEV_DONE") == "true": points_earned += 15
        current_score += points_earned
        with open("score.txt", "w") as f: f.write(str(current_score))
    return current_score, points_earned

# --- 7. Generate Dashboard OR Send Evening Email ---
def execute_pipeline(is_evening):
    quote = get_groq_motivation()
    news = get_tech_news()
    dsa_pattern_html = get_dsa_pattern()
    workout = get_todays_workout()
    custom_task = get_custom_focus()
    score, points = manage_score(is_evening)
    
    sender_email = os.environ.get("EMAIL_USER")
    sender_password = os.environ.get("EMAIL_PASS")
    dashboard_url = os.environ.get("DASHBOARD_URL", "#")

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = sender_email
    
    if is_evening:
        # EVENING CHECK-IN: Still sends the email with your XP breakdown
        msg['Subject'] = f"✅ Daily Wrap-Up: +{points} XP Earned! (Total: {score})"
        html = f"<h2>End of Day Review</h2><h3>+{points} XP! Total Consistency: {score} XP</h3><p>Your focus for tomorrow has been logged.</p>"
        msg.attach(MIMEText(html, 'html'))
    else:
        # MORNING BRIEF: Generate animated index.html
        dashboard_html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Morning Command Center</title>
            <script src="https://cdn.tailwindcss.com"></script>
            <style>
                body {{ background-color: #0f172a; color: #f8fafc; font-family: 'Inter', sans-serif; }}
                .animate-slide-up {{ opacity: 0; transform: translateY(20px); animation: slideUp 0.8s ease-out forwards; }}
                @keyframes slideUp {{ to {{ opacity: 1; transform: translateY(0); }} }}
                .delay-1 {{ animation-delay: 0.2s; }}
                .delay-2 {{ animation-delay: 0.4s; }}
                .delay-3 {{ animation-delay: 0.6s; }}
                .delay-4 {{ animation-delay: 0.8s; }}
                .delay-5 {{ animation-delay: 1.0s; }}
                .glass-card {{ background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.1); }}
            </style>
        </head>
        <body class="min-h-screen p-6 md:p-12">
            <div class="max-w-4xl mx-auto">
                <header class="text-center mb-12 animate-slide-up">
                    <h1 class="text-5xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400 mb-4">Good Morning.</h1>
                    <p class="text-xl text-gray-400 italic">"{quote}"</p>
                    <div class="mt-6 inline-block bg-blue-900/50 border border-blue-500/30 rounded-full px-6 py-2">
                        <span class="text-blue-300 font-bold">Total XP: {score} 🏆</span>
                    </div>
                </header>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div class="glass-card rounded-2xl p-6 shadow-xl animate-slide-up delay-1">
                        <h2 class="text-xl font-semibold text-white mb-4 border-b border-gray-700 pb-2">🎯 Today's Mission</h2>
                        <p class="text-lg text-emerald-400 font-medium">{custom_task}</p>
                    </div>

                    <div class="glass-card rounded-2xl p-6 shadow-xl animate-slide-up delay-2">
                        <h2 class="text-xl font-semibold text-white mb-4 border-b border-gray-700 pb-2">🧠 DSA Target</h2>
                        {dsa_pattern_html}
                    </div>

                    <div class="glass-card rounded-2xl p-6 shadow-xl animate-slide-up delay-3 md:col-span-2">
                        <h2 class="text-xl font-semibold text-white mb-4 border-b border-gray-700 pb-2">💪 Gym Protocol: {datetime.today().strftime('%A')}</h2>
                        {workout}
                    </div>

                    <div class="glass-card rounded-2xl p-6 shadow-xl animate-slide-up delay-4 md:col-span-2">
                        <h2 class="text-xl font-semibold text-white mb-4 border-b border-gray-700 pb-2">📰 Tech Radar</h2>
                        {news}
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        # Save the generated HTML to the repo
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(dashboard_html)
            
        # Send sleek "Notification" Email
        msg['Subject'] = f"🚀 Morning Brief is Live ({score} XP)"
        email_html = f"""
        <html><body style="font-family: Arial, sans-serif; background: #f3f4f6; padding: 40px; text-align: center;">
            <h2 style="color: #111827;">Your Animated Dashboard is Ready</h2>
            <a href="{dashboard_url}" style="display: inline-block; background: #2563eb; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; margin-top: 20px;">Open Morning Command Center</a>
        </body></html>
        """
        msg.attach(MIMEText(email_html, 'html'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        print("Pipeline Execution Complete!")
    except Exception as e:
        print(f"Failed to send email: {e}")

if __name__ == "__main__":
    is_evening = len(sys.argv) > 1 and sys.argv[1] == "--evening"
    execute_pipeline(is_evening)
