import json
import datetime
import os
import smtplib
import re
import html
from zoneinfo import ZoneInfo
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Try to get credentials, allow DRY_RUN for local testing without emails
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_APP_PASSWORD")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"

DAYS_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

def send_email(subject, html_body):
    if DRY_RUN:
        print(f"DRY RUN ENABLED. Would have sent email with subject: {subject}")
        with open("preview.html", "w", encoding="utf-8") as f:
            f.write(html_body)
        print("Wrote output to preview.html")
        return

    if not SENDER_EMAIL or not SENDER_PASSWORD or not RECEIVER_EMAIL:
        raise ValueError("Missing environment variables! Cannot send email.")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"College Timetable Notifier <{SENDER_EMAIL}>"
    msg["To"] = RECEIVER_EMAIL
    msg.attach(MIMEText(html_body, "html"))

    print(f"Connecting to SMTP server for {SENDER_EMAIL}...")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
    print(f"Email sent successfully to {RECEIVER_EMAIL}!")

def check_task_match(task_subject, lecture_subject):
    if "Break" in lecture_subject:
        return False
    # Extract short code inside parentheses, or use full subject
    short_code = task_subject.split("(")[-1].replace(")", "").strip() if "(" in task_subject else task_subject
    
    # Use Regex Word Boundaries to prevent partial matches (e.g., 'DB' matching 'DBMS')
    pattern = rf'\b{re.escape(short_code)}\b'
    if re.search(pattern, lecture_subject, re.IGNORECASE):
        return True
    return task_subject.lower() in lecture_subject.lower()

def render_lecture_rows(lectures):
    if not lectures:
        return "<tr><td colspan='3' style='padding: 12px; text-align: center; color: #666;'>No lectures scheduled!</td></tr>"
    
    rows = ""
    for l in lectures:
        is_break = "Break" in l.get("subject", "")
        bg_style = "background-color: #f8f9fa;" if is_break else ""
        rows += f"""
        <tr style="border-bottom: 1px solid #eee; {bg_style}">
            <td style="padding: 10px; font-weight: bold; color: #2c3e50;">{html.escape(l.get('time', ''))}</td>
            <td style="padding: 10px; color: #2980b9;">{html.escape(l.get('subject', ''))}</td>
            <td style="padding: 10px; color: #7f8c8d;">{html.escape(l.get('faculty', '-'))} ({html.escape(l.get('room', '-'))})</td>
        </tr>
        """
    return rows

def render_alert_card(task, lecture, alert_type):
    task_id = task.get("id", "?")
    faculty = html.escape(lecture.get("faculty", "Faculty"))
    subject = html.escape(lecture.get("subject", ""))
    task_text = html.escape(task.get("task", ""))

    if alert_type == "URGENT":
        bg, border, text_color = "#fce4e4", "#e74c3c", "#c0392b"
        header = f"🚨 URGENT: DUE TODAY — {subject}"
        footer = f"👉 You have this class TODAY! Complete it before entering class. (ID #{task_id})"
    elif alert_type == "ADVANCE":
        bg, border, text_color = "#fff9e6", "#f39c12", "#d68910"
        header = f"⏳ ADVANCE NOTICE: DUE TOMORROW — {subject}"
        footer = f"👉 Finish it today so you aren't rushed tomorrow morning. (ID #{task_id})"
    else: # WEEKEND
        bg, border, text_color = "#fff3cd", "#e74c3c", "#c0392b"
        header = f"⚠️ TASK DUE ON MONDAY: {subject}"
        footer = f"👉 Prepare and complete this over the weekend! (ID #{task_id})"

    return f"""
    <div style="background-color: {bg}; border-left: 5px solid {border}; padding: 14px; margin-bottom: 12px; border-radius: 4px;">
        <strong style="color: {text_color}; font-size: 15px;">{header}</strong><br/>
        <p style="margin: 6px 0; color: #2c3e50;">
            <strong>Faculty:</strong> {faculty}<br/>
            <strong>Task:</strong> <span style="color: {border}; font-weight: bold;">{task_text}</span>
        </p>
        <p style="margin: 0; color: #555; font-size: 12px; font-style: italic;">{footer}</p>
    </div>
    """

def load_json_or_fail(filename, default_val):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"CRITICAL ERROR loading {filename}: {e}")
        raise

def build_briefing():
    ist_now = datetime.datetime.now(ZoneInfo("Asia/Kolkata"))
    today_name = ist_now.strftime("%A")
    current_hour = ist_now.hour

    is_friday_night = (today_name == "Friday" and current_hour >= 18)
    is_weekend = today_name in ["Saturday", "Sunday"] or is_friday_night

    today_idx = DAYS_ORDER.index(today_name)
    tomorrow_name = DAYS_ORDER[(today_idx + 1) % 7]

    timetable = load_json_or_fail("timetable.json", {})
    tasks = load_json_or_fail("tasks.json", [])
    pending_tasks = [t for t in tasks if t.get("status") == "pending"]

    alert_section = ""
    other_pending_section = ""
    alerted_task_ids = set() # Prevent duplicate warnings for the same task

    if is_weekend:
        target_lectures = timetable.get("Monday", [])
        time_label = "Friday Evening Preview" if is_friday_night else f"Weekend Update ({today_name})"
        banner_title = f"🏖️ {time_label} — Preparation for Monday"
        table_title = "📚 Upcoming Monday Schedule"
        email_subject_prefix = "🏖️ Weekend Preview: Monday Schedule"

        for l in target_lectures:
            for t in pending_tasks:
                t_id = t.get("id")
                if t_id not in alerted_task_ids and check_task_match(t.get("subject", ""), l.get("subject", "")):
                    alert_section += render_alert_card(t, l, "WEEKEND")
                    alerted_task_ids.add(t_id)

    else:
        today_lectures = timetable.get(today_name, [])
        tomorrow_lectures = timetable.get(tomorrow_name, []) if tomorrow_name not in ["Saturday", "Sunday"] else []
        
        banner_title = f"📅 College Daily Briefing ({today_name})"
        table_title = "📚 Today's Schedule"
        target_lectures = today_lectures
        email_subject_prefix = f"📚 CSE Daily Schedule ({today_name})"

        # Today's Due Alerts
        for l in today_lectures:
            for t in pending_tasks:
                t_id = t.get("id")
                if t_id not in alerted_task_ids and check_task_match(t.get("subject", ""), l.get("subject", "")):
                    alert_section += render_alert_card(t, l, "URGENT")
                    alerted_task_ids.add(t_id)

        # Tomorrow's Advance Alerts
        for l in tomorrow_lectures:
            for t in pending_tasks:
                t_id = t.get("id")
                if t_id not in alerted_task_ids and check_task_match(t.get("subject", ""), l.get("subject", "")):
                    alert_section += render_alert_card(t, l, "ADVANCE")
                    alerted_task_ids.add(t_id)

    if alert_section:
        email_subject = f"⚠️ [ACTION REQUIRED] Timetable & Pending Work"
    else:
        alert_section = "<p style='color: #27ae60; font-weight: bold;'>✅ All clear! No pending tasks flagged for the upcoming schedule.</p>"
        email_subject = email_subject_prefix

    # Generate "Other Pending Tasks" footer for tasks not alerted today
    other_tasks = [t for t in pending_tasks if t.get("id") not in alerted_task_ids]
    if other_tasks:
        other_pending_section = "<h4 style='color: #7f8c8d; margin-top: 20px; border-top: 1px solid #eee; padding-top: 10px;'>📌 Other Pending Tasks (Not Due Immediately)</h4><ul style='color: #555; font-size: 13px;'>"
        for ot in other_tasks:
            other_pending_section += f"<li><strong>{html.escape(ot.get('subject', ''))}:</strong> {html.escape(ot.get('task', ''))} <em>(ID: {ot.get('id', '?')})</em></li>"
        other_pending_section += "</ul>"

    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f4f6f9; padding: 20px;">
        <div style="max-width: 650px; margin: 0 auto; background: #ffffff; border-radius: 8px; padding: 24px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <h2 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">{banner_title}</h2>
            
            <h3 style="color: #c0392b;">🚨 Homework & Task Alerts</h3>
            {alert_section}

            <br/>
            <h3 style="color: #34495e;">{table_title}</h3>
            <table style="width: 100%; border-collapse: collapse; text-align: left;">
                <thead>
                    <tr style="background-color: #2c3e50; color: #ffffff;">
                        <th style="padding: 10px;">Time</th>
                        <th style="padding: 10px;">Subject / Event</th>
                        <th style="padding: 10px;">Faculty & Room</th>
                    </tr>
                </thead>
                <tbody>
                    {render_lecture_rows(target_lectures)}
                </tbody>
            </table>
            
            {other_pending_section}

            <hr style="border: none; border-top: 1px solid #eee; margin-top: 30px;"/>
            <p style="font-size: 11px; color: #aaa; text-align: center;">Automated Alert • S4 Batch • GitHub Actions</p>
        </div>
    </body>
    </html>
    """

    send_email(email_subject, html_body)

if __name__ == "__main__":
    build_briefing()
