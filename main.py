import os
import sys
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests
from datetime import datetime
from groq import Groq

# --- 1. Fetch Motivation (Groq LLM) ---
def get_groq_motivation():
    try:
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a high-performance coach. Give a short, hard-hitting, 2-sentence motivational quote about discipline and consistency."
                }
            ],
            model="llama-3.1-8b-instant",
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return "Discipline equals freedom. Execute the plan."

# --- 2. Fetch Top 5 Tech News (NewsAPI) ---
def get_tech_news():
    api_key = os.environ.get("NEWS_API_KEY")
    url = f"https://newsapi.org/v2/top-headlines?country=us&category=technology&apiKey={api_key}"
    try:
        response = requests.get(url)
        articles = response.json().get("articles", [])[:5]
        news_html = "<ul style='padding-left: 20px;'>"
        for article in articles:
            news_html += f"<li style='margin-bottom: 10px;'><a href='{article['url']}' style='color: #2563eb; text-decoration: none;'>{article['title']}</a></li>"
        news_html += "</ul>"
        return news_html
    except Exception as e:
        return "<p>Could not fetch news today.</p>"

# --- 3. Fetch Competitive Edge (LeetCode) ---
def get_leetcode_daily():
    url = "https://leetcode.com/graphql"
    query = """
    query questionOfToday {
        activeDailyCodingChallengeQuestion {
            link
            question { title difficulty topicTags { name } }
        }
    }
    """
    try:
        response = requests.post(url, json={"query": query})
        data = response.json()["data"]["activeDailyCodingChallengeQuestion"]
        q_data = data["question"]
        topics = ", ".join([tag["name"] for tag in q_data["topicTags"]])
        return {
            "title": q_data["title"],
            "difficulty": q_data["difficulty"],
            "link": "https://leetcode.com" + data["link"],
            "topics": topics
        }
    except Exception as e:
        return {"title": "Error fetching LeetCode", "difficulty": "N/A", "link": "#", "topics": "N/A"}

# --- 4. Determine Gym Habit (Dynamic via Groq for Commercial Gym) ---
def get_todays_workout():
    workouts_focus = {
        "Monday": "Chest and Biceps",
        "Tuesday": "Legs and Shoulders",
        "Wednesday": "Back and Triceps",
        "Thursday": "Rest Day",
        "Friday": "Thighs and Biceps", 
        "Saturday": "Core and Forearms",
        "Sunday": "Rest Day"
    }
    
    today = datetime.today().strftime('%A')
    focus_for_today = workouts_focus.get(today, "Rest Day")

    if "Rest" in focus_for_today:
        return f"<p><strong>{focus_for_today}</strong>. Focus on hydration, stretching, and recovery today.</p>"

    try:
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        prompt = (
            f"I am working out at a fully equipped commercial gym. Today's target muscle groups are: {focus_for_today}. "
            "Generate a strict, HTML-formatted unordered list (<ul><li>...</li></ul>) of 5 to 6 exact exercises "
            "I need to do today to target these specific muscles. Utilize a mix of barbells, machines, cables, and dumbbells. "
            "Include specific sets and reps (e.g., 4x10). Do not include any intro or outro text, just the HTML list."
        )
        
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system", 
                    "content": "You are a precise, no-nonsense fitness coach. Output only the requested HTML."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            model="llama-3.1-8b-instant",
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"<p>Error fetching dynamic workout. Target muscles for today: {focus_for_today}</p>"

# --- 5. Scoring System ---
def manage_score(is_evening_check_in):
    score_file = "score.txt"
    try:
        with open(score_file, "r") as f:
            current_score = int(f.read().strip())
    except FileNotFoundError:
        current_score = 0
    except ValueError:
        current_score = 0
    
    if is_evening_check_in:
        current_score += 10 # +10 points for completing the day
        with open(score_file, "w") as f:
            f.write(str(current_score))
            
    return current_score

# --- 6. Send Email ---
def send_email(is_evening):
    # Fetch Data
    quote = get_groq_motivation()
    news = get_tech_news()
    lc_data = get_leetcode_daily()
    workout = get_todays_workout()
    score = manage_score(is_evening)
    
    sender_email = os.environ.get("EMAIL_USER")
    sender_password = os.environ.get("EMAIL_PASS")

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = sender_email
    
    # Configure subject and headers based on time of day
    if is_evening:
        msg['Subject'] = f"✅ Daily Wrap-Up: Score Updated ({score} XP)"
        header_text = "End of Day Review"
        action_text = f"<h3 style='color: #10b981;'>+10 XP Earned! Current Consistency Score: {score} XP 🏆</h3>"
    else:
        msg['Subject'] = f"🚀 Morning Brief: Mission Start ({score} XP)"
        header_text = "Good Morning, Farhan!"
        action_text = f"<h3 style='color: #4f46e5;'>Current Consistency Score: {score} XP 🏆</h3><p style='color: #6b7280; font-size: 0.9em;'><em>Trigger your evening action at midnight to log your points!</em></p>"

    # HTML Email Template
    html = f"""
    <html>
      <head>
        <style>
          body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f3f4f6; padding: 20px; }}
          .container {{ max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; padding: 30px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
          .header {{ text-align: center; color: #111827; border-bottom: 2px solid #e5e7eb; padding-bottom: 20px; margin-bottom: 20px; }}
          h2 {{ color: #374151; margin-top: 25px; border-bottom: 2px solid #f3f4f6; padding-bottom: 8px; font-size: 1.25em; }}
          .quote-box {{ background: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; font-style: italic; font-size: 1.1em; color: #92400e; margin: 20px 0; border-radius: 4px; }}
          .task-box {{ background: #f9fafb; padding: 15px; border-radius: 8px; border: 1px solid #e5e7eb; margin-bottom: 15px; }}
          .tag {{ background: #e0e7ff; color: #4338ca; padding: 4px 8px; border-radius: 4px; font-size: 0.85em; font-weight: bold; }}
          .diff-easy {{ color: #10b981; font-weight: bold; text-transform: capitalize; }}
          .diff-medium {{ color: #f59e0b; font-weight: bold; text-transform: capitalize; }}
          .diff-hard {{ color: #ef4444; font-weight: bold; text-transform: capitalize; }}
          a.btn {{ display: inline-block; background: #2563eb; color: white; text-decoration: none; padding: 10px 20px; border-radius: 6px; margin-top: 10px; font-weight: bold; }}
        </style>
      </head>
      <body>
        <div class="container">
          <div class="header">
            <h1>{header_text}</h1>
          </div>
          
          <div class="quote-box">
            "{quote}"
          </div>
          
          <div style="text-align: center; margin: 20px 0; padding: 15px; background: #f0fdf4; border-radius: 8px; border: 1px solid #bbf7d0;">
            {action_text}
          </div>

          <h2>📰 Top 5 Tech News</h2>
          <div class="task-box">
            {news}
          </div>

          <h2>🧠 Competitive Edge (DSA)</h2>
          <div class="task-box">
            <p style="font-size: 1.1em; margin-bottom: 5px;"><strong>{lc_data['title']}</strong></p>
            <p style="margin-bottom: 10px;"><strong>Difficulty:</strong> <span class="diff-{lc_data['difficulty'].lower()}">{lc_data['difficulty']}</span></p>
            <p style="margin-bottom: 15px;"><strong>Topics:</strong> <span class="tag">{lc_data['topics']}</span></p>
            <a href="{lc_data['link']}" class="btn">Solve on LeetCode</a>
          </div>

          <h2>💪 Gym Protocol: {datetime.today().strftime('%A')}</h2>
          <div class="task-box">
            {workout}
          </div>
          
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
        print(f"Error sending email: {e}")

if __name__ == "__main__":
    # If script is run with 'python main.py --evening', it adds points and sends evening wrap-up
    is_evening = len(sys.argv) > 1 and sys.argv[1] == "--evening"
    
    print("Initiating build sequence...")
    send_email(is_evening)
    print("Execution complete.")
