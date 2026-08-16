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
        news_html = "<ul class='space-y-3 font-tech text-[1.02rem]'>"
        for item in root.findall('./channel/item')[:5]:
            title_node = item.find('title')
            link_node = item.find('link')
            title = title_node.text if title_node is not None else "News Headline"
            link = link_node.text if link_node is not None else "#"
            news_html += f"<li class='flex gap-3'><span class='text-[rgb(var(--cyan))] font-mono'>▸</span><a href='{link}' target='_blank' class='link-glow'>{title}</a></li>"
        news_html += "</ul>"
        return news_html
    except Exception:
        return "<p class='text-slate-400 font-tech'>Could not fetch news today.</p>"

# --- 3. Format Dual-Pattern Revision HTML ---
def format_revision_card_html(rev):
    primary = rev.get("primary", "")
    subsidiary = rev.get("subsidiary", "")
    takeaway = rev.get("headline_takeaway", "")
    week_num = rev.get("week_number", 1)
    day_num = rev.get("day_in_week", 1)
    
    html = f"""
    <div class="mb-4">
        <div class="flex flex-wrap items-center gap-2 mb-4">
            <span class="badge badge-emerald font-mono">Week {week_num} · Day {day_num} of 7</span>
            <span class="badge badge-magenta font-mono">{primary} &amp; {subsidiary}</span>
        </div>
        <h3 class="font-tech text-xl md:text-2xl font-bold text-[rgb(var(--amber))]" style="text-shadow:0 0 14px rgba(var(--amber),0.5)">
            💡 {takeaway}
        </h3>
    """
    
    if rev.get("visual_trigger"):
        html += f"<p class='font-tech text-slate-300 text-lg mt-3'><strong class='text-white'>Visual Trigger:</strong> {rev['visual_trigger']}</p>"
    if rev.get("plain_rule"):
        html += f"<p class='font-tech text-slate-300 text-lg mt-2'><strong class='text-white'>Plain-English Rule:</strong> {rev['plain_rule']}</p>"
    if rev.get("worked_micro_example"):
        html += f"<p class='font-mono text-slate-400 text-sm mt-2 italic'><strong class='text-slate-300'>Walkthrough:</strong> {rev['worked_micro_example']}</p>"
    if rev.get("connection_bridge"):
        html += f"<p class='font-tech text-slate-300 text-lg mt-2'><strong class='text-white'>Connection Bridge:</strong> {rev['connection_bridge']}</p>"
    if rev.get("boundary_switch"):
        html += f"<p class='font-tech text-slate-300 text-lg mt-2'><strong class='text-white'>Boundary Switch:</strong> {rev['boundary_switch']}</p>"
    if rev.get("problem_statement"):
        html += f"<p class='font-tech text-slate-300 text-lg mt-2'><strong class='text-white'>Mixed Problem:</strong> {rev['problem_statement']}</p>"
        if rev.get("solution_sketch"):
            html += f"<p class='font-mono text-slate-400 text-sm mt-1 italic'><strong class='text-slate-300'>Approach:</strong> {rev['solution_sketch']}</p>"
    if rev.get("quiz_question"):
        html += f"<p class='font-tech text-slate-300 text-lg mt-2'><strong class='text-white'>Recall Quiz:</strong> {rev['quiz_question']}</p>"
        html += f"<p class='font-tech text-[rgb(var(--emerald))] text-lg mt-1'><strong class='text-white'>Answer:</strong> {rev.get('quiz_answer', '')}</p>"
        
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
        return f"<p class='font-tech text-lg text-slate-300'><strong class='text-white'>{focus}.</strong> Focus on hydration, stretching, and recovery today.</p>"
    try:
        api_key = os.environ.get("GROQ_API_KEY", "")
        if not api_key:
            return f"<p class='font-tech text-lg text-slate-300'><strong class='text-white'>Focus today:</strong> {focus}</p>"
        client = Groq(api_key=api_key)
        chat = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Fitness coach. Output HTML list only."}, 
                {"role": "user", "content": f"At a gym, target: {focus}. Give 5 exercises (barbells/cables/machines) with sets/reps as a <ul class='space-y-2 font-tech text-slate-300 text-[1.02rem]'><li> list. No intro."}
            ],
            model="llama-3.1-8b-instant",
        )
        return chat.choices[0].message.content
    except Exception: 
        return f"<p class='font-tech text-lg text-slate-300'><strong class='text-white'>Focus today:</strong> {focus}</p>"

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

    # Generate Cyberpunk Three.js Animated index.html Command Center
    dashboard_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CONSIS v2.0 — Morning Command Center</title>
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@600;800&family=Rajdhani:wght@500;600;700&family=JetBrains+Mono:wght@400;500;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
    :root{{
        --void:#030712;
        --cyan:0,240,255;
        --emerald:0,255,136;
        --magenta:255,0,127;
        --amber:255,183,0;
    }}
    *{{box-sizing:border-box;}}
    html{{scroll-behavior:smooth;}}
    body{{
        background:var(--void);
        color:#e6f1ff;
        font-family:'Inter', sans-serif;
        min-height:100vh;
        overflow-x:hidden;
        position:relative;
    }}
    .font-display{{ font-family:'Orbitron', sans-serif; }}
    .font-tech{{ font-family:'Rajdhani', sans-serif; }}
    .font-mono{{ font-family:'JetBrains Mono', monospace; }}

    #bgCanvas{{ position:fixed; inset:0; z-index:0; display:block; }}
    .bg-grid{{
        position:fixed; inset:0; z-index:1; pointer-events:none;
        background-image:
            linear-gradient(rgba(0,240,255,0.06) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0,240,255,0.06) 1px, transparent 1px);
        background-size:44px 44px;
        mask-image:radial-gradient(ellipse 80% 60% at 50% 20%, black 40%, transparent 90%);
        -webkit-mask-image:radial-gradient(ellipse 80% 60% at 50% 20%, black 40%, transparent 90%);
    }}
    .scanlines{{
        position:fixed; inset:0; z-index:2; pointer-events:none; opacity:0.25;
        background:repeating-linear-gradient(0deg, rgba(255,255,255,0.025) 0px, rgba(255,255,255,0.025) 1px, transparent 1px, transparent 3px);
    }}
    #scanProgress{{
        position:fixed; top:0; left:0; height:3px; width:0%; z-index:100;
        background:linear-gradient(90deg, rgb(var(--cyan)), rgb(var(--magenta)), rgb(var(--amber)));
        box-shadow:0 0 12px rgba(var(--cyan),0.8);
        transition:width 0.08s linear;
    }}
    .content{{ position:relative; z-index:10; }}

    .panel{{
        position:relative;
        background:linear-gradient(160deg, rgba(9,13,22,0.72), rgba(9,13,22,0.5));
        backdrop-filter:blur(18px);
        -webkit-backdrop-filter:blur(18px);
        border:1px solid rgba(var(--cyan),0.18);
        border-radius:18px;
        transition:transform 0.35s cubic-bezier(.16,.84,.44,1), border-color 0.35s ease, box-shadow 0.35s ease;
    }}
    .panel:hover{{
        transform:translateY(-4px);
        border-color:rgba(var(--cyan),0.45);
        box-shadow:0 0 0 1px rgba(var(--cyan),0.15), 0 20px 50px -20px rgba(var(--cyan),0.35);
    }}
    .corner{{ position:absolute; width:18px; height:18px; pointer-events:none; opacity:0.9; }}
    .corner.tl{{ top:-1px; left:-1px; border-top:2px solid; border-left:2px solid; border-top-left-radius:6px; }}
    .corner.tr{{ top:-1px; right:-1px; border-top:2px solid; border-right:2px solid; border-top-right-radius:6px; }}
    .corner.bl{{ bottom:-1px; left:-1px; border-bottom:2px solid; border-left:2px solid; border-bottom-left-radius:6px; }}
    .corner.br{{ bottom:-1px; right:-1px; border-bottom:2px solid; border-right:2px solid; border-bottom-right-radius:6px; }}
    .accent-cyan .corner{{ border-color:rgb(var(--cyan)); filter:drop-shadow(0 0 4px rgba(var(--cyan),0.8)); }}
    .accent-emerald .corner{{ border-color:rgb(var(--emerald)); filter:drop-shadow(0 0 4px rgba(var(--emerald),0.8)); }}
    .accent-amber .corner{{ border-color:rgb(var(--amber)); filter:drop-shadow(0 0 4px rgba(var(--amber),0.8)); }}

    .divider{{ height:1px; background:linear-gradient(90deg, rgba(var(--cyan),0.5), transparent); }}

    .glow-title{{ text-shadow:0 0 18px rgba(var(--cyan),0.55), 0 0 40px rgba(var(--magenta),0.25); }}
    .badge{{
        display:inline-flex; align-items:center; gap:6px;
        font-size:0.72rem; letter-spacing:0.06em; padding:5px 12px; border-radius:100px;
        border:1px solid; text-transform:uppercase;
    }}
    .badge .dot{{ width:6px; height:6px; border-radius:50%; box-shadow:0 0 8px currentColor; }}
    .badge-cyan{{ color:rgb(var(--cyan)); border-color:rgba(var(--cyan),0.4); background:rgba(var(--cyan),0.08); box-shadow:0 0 14px -4px rgba(var(--cyan),0.5); }}
    .badge-emerald{{ color:rgb(var(--emerald)); border-color:rgba(var(--emerald),0.4); background:rgba(var(--emerald),0.08); box-shadow:0 0 14px -4px rgba(var(--emerald),0.5); }}
    .badge-magenta{{ color:rgb(var(--magenta)); border-color:rgba(var(--magenta),0.4); background:rgba(var(--magenta),0.08); box-shadow:0 0 14px -4px rgba(var(--magenta),0.5); }}
    .badge-amber{{ color:rgb(var(--amber)); border-color:rgba(var(--amber),0.45); background:rgba(var(--amber),0.1); box-shadow:0 0 14px -4px rgba(var(--amber),0.5); }}
    .pulse{{ animation:pulseDot 2s ease-in-out infinite; }}
    @keyframes pulseDot{{ 0%,100%{{ opacity:1; }} 50%{{ opacity:0.35; }} }}

    .xp-pill{{
        border:1px solid rgba(var(--amber),0.5);
        background:linear-gradient(135deg, rgba(var(--amber),0.15), rgba(var(--amber),0.03));
        box-shadow:0 0 25px -6px rgba(var(--amber),0.6), inset 0 0 20px -12px rgba(var(--amber),0.8);
    }}

    .link-glow{{ color:rgb(var(--cyan)); text-decoration:none; transition:text-shadow 0.25s ease, color 0.25s ease; }}
    .link-glow:hover{{ color:#7fe9ff; text-shadow:0 0 10px rgba(var(--cyan),0.8); }}

    .reveal{{ opacity:0; transform:translateY(26px); transition:opacity 0.8s cubic-bezier(.16,.84,.44,1), transform 0.8s cubic-bezier(.16,.84,.44,1); }}
    .reveal.in{{ opacity:1; transform:translateY(0); }}

    @media (prefers-reduced-motion: reduce){{
        *{{ animation-duration:0.01ms !important; transition-duration:0.01ms !important; }}
    }}
</style>
</head>
<body class="min-h-screen p-6 md:p-12">

<canvas id="bgCanvas"></canvas>
<div class="bg-grid"></div>
<div class="scanlines"></div>
<div id="scanProgress"></div>

<div class="content max-w-4xl mx-auto">

    <header class="text-center mb-14 reveal" data-idx="0">
        <div class="font-mono text-xs tracking-[0.3em] text-cyan-300/70 mb-3 uppercase">// Consis v2.0 — Morning Command Center</div>
        <h1 class="font-display glow-title text-4xl md:text-6xl font-extrabold text-white mb-5 tracking-wide">Good Morning<span class="text-[rgb(var(--cyan))]">.</span></h1>
        <p class="font-tech text-lg md:text-xl text-slate-300/90 italic max-w-2xl mx-auto leading-relaxed">"{quote}"</p>
        <div class="xp-pill mt-7 inline-flex items-center gap-2 rounded-full px-6 py-2.5 font-mono">
            <span class="text-[rgb(var(--amber))] font-bold tracking-wide">TOTAL XP: {score}</span>
            <span>🏆</span>
        </div>
    </header>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">

        <!-- Today's Mission -->
        <div class="panel accent-emerald reveal p-6 shadow-xl" data-idx="1">
            <span class="corner tl"></span><span class="corner tr"></span><span class="corner bl"></span><span class="corner br"></span>
            <div class="flex items-center justify-between mb-4">
                <h2 class="font-tech text-xl font-bold text-white tracking-wide">🎯 Today's Mission</h2>
                <span class="badge badge-emerald"><span class="dot pulse" style="background:rgb(var(--emerald))"></span>Active</span>
            </div>
            <div class="divider mb-4"></div>
            <p class="font-mono text-2xl text-[rgb(var(--emerald))] font-semibold" style="text-shadow:0 0 16px rgba(var(--emerald),0.5)">{custom_task}</p>
        </div>

        <!-- Daily DSA Revision -->
        <div class="panel accent-cyan reveal p-6 shadow-xl md:col-span-2" data-idx="2">
            <span class="corner tl"></span><span class="corner tr"></span><span class="corner bl"></span><span class="corner br"></span>
            <div class="flex items-center justify-between mb-4 flex-wrap gap-2">
                <h2 class="font-tech text-xl font-bold text-white tracking-wide">🧠 Daily DSA Revision <span class="text-slate-400 font-medium text-base">(Dual-Pattern)</span></h2>
                <span class="badge badge-cyan"><span class="dot pulse" style="background:rgb(var(--cyan))"></span>Live</span>
            </div>
            <div class="divider mb-5"></div>
            {revision_html}
        </div>

        <!-- Gym Protocol -->
        <div class="panel accent-amber reveal p-6 shadow-xl md:col-span-2" data-idx="3">
            <span class="corner tl"></span><span class="corner tr"></span><span class="corner bl"></span><span class="corner br"></span>
            <div class="flex items-center justify-between mb-4">
                <h2 class="font-tech text-xl font-bold text-white tracking-wide">💪 Gym Protocol: {today_name}</h2>
                <span class="badge badge-amber"><span class="dot pulse" style="background:rgb(var(--amber))"></span>Synced</span>
            </div>
            <div class="divider mb-4"></div>
            {workout}
        </div>

        <!-- Tech Radar -->
        <div class="panel accent-cyan reveal p-6 shadow-xl md:col-span-2" data-idx="4">
            <span class="corner tl"></span><span class="corner tr"></span><span class="corner bl"></span><span class="corner br"></span>
            <div class="flex items-center justify-between mb-4">
                <h2 class="font-tech text-xl font-bold text-white tracking-wide">📰 Tech Radar</h2>
                <span class="badge badge-cyan"><span class="dot pulse" style="background:rgb(var(--cyan))"></span>Synced</span>
            </div>
            <div class="divider mb-4"></div>
            {news}
        </div>

    </div>

    <footer class="text-center mt-12 font-mono text-xs text-slate-500 tracking-widest reveal" data-idx="5">
        // SYSTEM STATUS: NOMINAL &nbsp;·&nbsp; NEXT SYNC: TOMORROW 06:00 IST
    </footer>
</div>

<script>
const bar = document.getElementById('scanProgress');
function updateBar(){{
    const h = document.documentElement;
    const pct = h.scrollTop / (h.scrollHeight - h.clientHeight) * 100;
    bar.style.width = (isFinite(pct) ? pct : 0) + '%';
}}
document.addEventListener('scroll', updateBar, {{ passive:true }});
updateBar();

const items = document.querySelectorAll('.reveal');
const io = new IntersectionObserver((entries) => {{
    entries.forEach(entry => {{
        if(entry.isIntersecting){{
            const delay = parseInt(entry.target.dataset.idx || 0) * 120;
            setTimeout(() => entry.target.classList.add('in'), delay);
            io.unobserve(entry.target);
        }}
    }});
}}, {{ threshold: 0.12 }});
items.forEach(el => io.observe(el));

const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
const isSmall = innerWidth < 640;

let scene, camera, renderer, icosGroup, particles, clock;

function initThree(){{
    scene = new THREE.Scene();
    camera = new THREE.PerspectiveCamera(60, innerWidth / innerHeight, 0.1, 100);
    camera.position.z = 6.5;

    renderer = new THREE.WebGLRenderer({{ canvas: document.getElementById('bgCanvas'), antialias: true, alpha: true }});
    renderer.setSize(innerWidth, innerHeight);
    renderer.setPixelRatio(Math.min(devicePixelRatio, 2));

    const detail = isSmall ? 0 : 1;
    const geo = new THREE.IcosahedronGeometry(2.3, detail);
    const wireGeo = new THREE.WireframeGeometry(geo);
    const wireMat = new THREE.LineBasicMaterial({{ color: 0x00f0ff, transparent: true, opacity: 0.55 }});
    const wire = new THREE.LineSegments(wireGeo, wireMat);

    const fillMat = new THREE.MeshBasicMaterial({{ color: 0xff007f, transparent: true, opacity: 0.05, side: THREE.DoubleSide }});
    const fillMesh = new THREE.Mesh(geo, fillMat);

    icosGroup = new THREE.Group();
    icosGroup.add(wire, fillMesh);
    scene.add(icosGroup);

    const count = isSmall ? 350 : 700;
    const positions = new Float32Array(count * 3);
    const colors = new Float32Array(count * 3);
    const palette = [[0,240,255],[0,255,136],[255,0,127],[255,183,0]];
    for(let i = 0; i < count; i++){{
        const r = 5 + Math.random() * 9;
        const theta = Math.random() * Math.PI * 2;
        const phi = Math.acos((Math.random() * 2) - 1);
        positions[i*3]     = r * Math.sin(phi) * Math.cos(theta);
        positions[i*3 + 1] = r * Math.sin(phi) * Math.sin(theta);
        positions[i*3 + 2] = r * Math.cos(phi);
        const c = palette[Math.floor(Math.random() * palette.length)];
        colors[i*3] = c[0]/255; colors[i*3+1] = c[1]/255; colors[i*3+2] = c[2]/255;
    }}
    const pGeo = new THREE.BufferGeometry();
    pGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    pGeo.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    const pMat = new THREE.PointsMaterial({{
        size: 0.045, vertexColors: true, transparent: true, opacity: 0.85,
        blending: THREE.AdditiveBlending, depthWrite: false
    }});
    particles = new THREE.Points(pGeo, pMat);
    scene.add(particles);

    clock = new THREE.Clock();
}}

function scrollProgress(){{
    const h = document.documentElement;
    const denom = h.scrollHeight - h.clientHeight;
    return denom > 0 ? h.scrollTop / denom : 0;
}}

let mx = 0, my = 0;
addEventListener('mousemove', (e) => {{
    mx = (e.clientX / innerWidth - 0.5) * 2;
    my = (e.clientY / innerHeight - 0.5) * 2;
}});

function animate(){{
    requestAnimationFrame(animate);
    const t = clock.getElapsedTime();
    const p = scrollProgress();

    icosGroup.rotation.y = t * 0.12 + p * Math.PI * 1.4;
    icosGroup.rotation.x = t * 0.05 + p * Math.PI * 0.6;
    particles.rotation.y = -t * 0.03 - p * 0.8;

    camera.position.z = 6.5 - p * 2.2;
    camera.position.x += (mx * 0.6 - camera.position.x) * 0.04;
    camera.position.y += (-my * 0.4 - camera.position.y) * 0.04;
    camera.lookAt(0, 0, 0);

    renderer.render(scene, camera);
}}

function onResize(){{
    camera.aspect = innerWidth / innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(innerWidth, innerHeight);
}}

if(window.THREE){{
    initThree();
    addEventListener('resize', onResize);
    if(reduceMotion){{
        renderer.render(scene, camera);
    }} else {{
        animate();
    }}
}}
</script>
</body>
</html>"""

    # Save to both index.html and docs/index.html
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(dashboard_html)
    os.makedirs("docs", exist_ok=True)
    with open("docs/index.html", "w", encoding="utf-8") as f:
        f.write(dashboard_html)

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
                  body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0f172a; color: #e6f1ff; padding: 20px; }}
                  .container {{ max-width: 600px; margin: 0 auto; background: #1e293b; border-radius: 16px; padding: 30px; border: 1px solid #334155; }}
                  .header {{ text-align: center; color: #ffffff; border-bottom: 1px solid #334155; padding-bottom: 20px; margin-bottom: 20px; }}
                  .quote-box {{ background: rgba(245, 185, 66, 0.1); border-left: 4px solid #f5b942; padding: 15px; font-style: italic; font-size: 1.05em; color: #f5b942; margin: 20px 0; border-radius: 6px; }}
                  .btn {{ display: inline-block; background: linear-gradient(90deg, #00f0ff, #00ff88); color: #030712 !important; text-decoration: none; padding: 14px 28px; border-radius: 100px; font-weight: bold; margin: 15px 0; font-family: 'Segoe UI', sans-serif; }}
                  .task-box {{ background: rgba(15, 23, 42, 0.8); padding: 18px; border-radius: 12px; border: 1px solid #334155; margin-bottom: 15px; }}
                  h2 {{ color: #00f0ff; margin-top: 25px; border-bottom: 1px solid #334155; padding-bottom: 8px; font-size: 1.2em; }}
                </style>
              </head>
              <body>
                <div class="container">
                  <div class="header">
                    <h1 style="margin-bottom: 10px; font-size: 26px;">Good Morning, Farhan! 🚀</h1>
                    <a href="{dashboard_url}" target="_blank" class="btn">🌐 Open Cyberpunk 3D Command Center</a>
                  </div>
                  
                  <div class="quote-box">
                    "{quote}"
                  </div>

                  <div style="text-align: center; margin: 20px 0; padding: 15px; background: rgba(0, 255, 136, 0.1); border-radius: 10px; border: 1px solid rgba(0, 255, 136, 0.3);">
                    <h3 style="color: #00ff88; margin: 0;">Total Consistency Score: {score} XP 🏆</h3>
                  </div>

                  <h2>🎯 Today's Mission</h2>
                  <div class="task-box">
                    <p style="color: #00ff88; font-weight: bold; font-size: 1.15em; margin: 0;">{custom_task}</p>
                  </div>

                  <h2>🧠 Daily DSA Revision (Dual-Pattern)</h2>
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

                  <div style="text-align: center; margin-top: 25px; padding-top: 20px; border-top: 1px solid #334155;">
                    <a href="{dashboard_url}" target="_blank" class="btn">🌐 Launch Cyberpunk 3D Dashboard</a>
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
