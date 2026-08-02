import os
import sys
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from groq import Groq

# --- 1. Fetch Motivation (Groq LLM) ---
def get_groq_motivation():
    try:
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        chat_completion = client.chat.completions.create(
            messages=[{"role": "system", "content": "You are a high-performance coach. Give a short, hard-hitting, 2-sentence motivational quote about discipline."}],
            model="llama-3.1-8b-instant",
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return "Discipline equals freedom. Execute the plan."

# --- 2. Fetch Tech News (TechCrunch RSS) ---
def get_tech_news():
    try:
        response = requests.get('https://techcrunch.com/feed/')
        root = ET.fromstring(response.content)
        news_html = "<ul style='padding-left: 20px; margin: 0;'>"
        for item in root.findall('./channel/item')[:5]:
            title = item.find('title').text
            link = item.find('link').text
            news_html += f"<li style='margin-bottom: 10px;'><a href='{link}' style='color: #2563eb; text-decoration: none;'>{title}</a></li>"
        news_html += "</ul>"
        return news_html
    except Exception as e:
        return "<p>Could not fetch news today.</p>"

# --- 3. Fetch DSA Pattern (Post-Trie Timetable) ---
def get_dsa_pattern():
    # Your brand new timetable
    patterns = {
        "Monday": "Graph Traversals (DFS & BFS)",
        "Tuesday": "Advanced Graphs (Shortest Path, Topological Sort)",
        "Wednesday": "Backtracking (Permutations, Combinations)",
        "Thursday": "1D Dynamic Programming",
        "Friday": "2D Dynamic Programming",
        "Saturday": "Union Find / Disjoint Sets",
        "Sunday": "Greedy Algorithms & Bit Manipulation"
    }
    today = datetime.today().strftime('%A')
    pattern = patterns.get(today, "General Review")
    
    try:
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        chat = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a senior technical interviewer. Given a DSA pattern, suggest exactly ONE classic LeetCode problem name and a 1-sentence technical tip. Output ONLY HTML in this format: <p><strong>Problem:</strong> [Name]</p><p><strong>Tip:</strong> [Tip]</p>"},
                {"role": "user", "content": f"The pattern is: {pattern}"}
            ],
            model="llama-3.1-8b-instant",
        )
        groq_tip = chat.choices[0].message.content
        return f"<h3 style='color: #2563eb; margin-top: 0; margin-bottom: 10px;'>{pattern}</h3>{groq_tip}"
    except Exception:
        return f"<h3 style='color: #2563eb; margin-top: 0; margin-bottom: 10px;'>{pattern}</h3><p>Focus on this pattern today!</p>"

# --- 4. Fetch Gym Routine ---
def get_todays_workout():
    workouts = {"Monday": "Chest and Biceps", "Tuesday": "Legs and Shoulders", "Wednesday": "Back and Triceps", "Thursday": "Rest Day", "Friday": "Thighs and Biceps", "Saturday": "Core and Forearms", "Sunday": "Rest Day"}
    focus = workouts.get(datetime.today().strftime('%A'), "Rest Day")
    if "Rest" in focus: return f"<p style='margin: 0;'><strong>{focus}</strong>. Focus on hydration and recovery.</p>"
    try:
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        chat = client.chat.completions.create(
            messages=[{"role": "system", "content": "You are a fitness coach. Output only an HTML list."}, 
                      {"role": "user", "content": f"At a commercial gym, target: {focus}. Give 5 exercises (barbells/cables/machines) with sets/reps as a <ul style='margin-bottom: 0;'><li> list. No intro."}],
            model="llama-3.1-8b-instant",
        )
        return chat.choices[0].message.content
    except Exception:
        return f"<p style='margin: 0;'>Focus today: {focus}</p>"

# --- 5. Fetch Custom Task ---
def get_custom_focus():
    try:
        with open("focus.txt", "r") as f:
            task = f.read().strip()
            return task if task else "No specific custom task set. Dominate the core habits!"
    except FileNotFoundError:
        return "No specific custom task set. Dominate the core habits!"

# --- 6. Dynamic Scoring System ---
def manage_score(is_evening):
    try:
        with open("score.txt", "r") as f:
            current_score = int(f.read().strip())
    except:
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

# --- 7. Send Email ---
def send_email(is_evening):
    quote = get_groq_motivation()
    news = get_tech_news()
    dsa_pattern_html = get_dsa_pattern()
    workout = get_todays_workout()
    custom_task = get_custom_focus()
    score, points = manage_score(is_evening)
    
    sender_email = os.environ.get("EMAIL_USER")
    sender_password = os.environ.get("EMAIL_PASS")

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = sender_email
    
    if is_evening:
        msg['Subject'] = f"✅ Daily Wrap-Up: +{points} XP Earned! (Total: {score})"
        header = f"End of Day Review: +{points} XP!"
        action = f"<h3 style='color: #10b981; margin: 0;'>Total Consistency Score: {score} XP 🏆</h3>"
    else:
        msg['Subject'] = f"🚀 Morning Brief: Mission Start ({score} XP)"
        header = "Good Morning!"
        action = f"<h3 style='color: #4f46e5; margin: 0;'>Total Consistency Score: {score} XP 🏆</h3><p style='color: #6b7280; font-size: 0.9em; margin-top: 5px; margin-bottom: 0;'><em>Trigger your evening action at midnight to log your points!</em></p>"

    html = f"""
    <html>
      <body style="font-family: 'Segoe UI', Tahoma, sans-serif; background: #f3f4f6; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; padding: 30px;">
          <h1 style="text-align: center; color: #111827; margin-top: 0;">{header}</h1>
          
          <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; font-style: italic; margin: 20px 0;">"{quote}"</div>
          <div style="text-align: center; background: #f0fdf4; border-radius: 8px; padding: 15px; margin-bottom: 20px;">{action}</div>
          
          <h2 style="color: #374151; border-bottom: 2px solid #f3f4f6; padding-bottom: 5px;">🎯 Today's Custom Focus</h2>
          <div style="background: #f9fafb; padding: 15px; border-radius: 8px; margin-bottom: 20px; font-size: 1.1em;"><strong>{custom_task}</strong></div>

          <h2 style="color: #374151; border-bottom: 2px solid #f3f4f6; padding-bottom: 5px;">🧠 DSA Pattern of the Day</h2>
          <div style="background: #f9fafb; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
            {dsa_pattern_html}
          </div>

          <h2 style="color: #374151; border-bottom: 2px solid #f3f4f6; padding-bottom: 5px;">💪 Gym Protocol: {datetime.today().strftime('%A')}</h2>
          <div style="background: #f9fafb; padding: 15px; border-radius: 8px; margin-bottom: 20px;">{workout}</div>

          <h2 style="color: #374151; border-bottom: 2px solid #f3f4f6; padding-bottom: 5px;">📰 Top 5 Tech News</h2>
          <div style="background: #f9fafb; padding: 15px; border-radius: 8px;">{news}</div>
        </div>
      </body>
    </html>
    """
    msg.attach(MIMEText(html, 'html'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

if __name__ == "__main__":
    is_evening = len(sys.argv) > 1 and sys.argv[1] == "--evening"
    send_email(is_evening)
