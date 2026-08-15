# Serverless Timetable & Task Pipeline

An event-driven, zero-maintenance notification system built to manage college schedules and pending assignments. It utilizes GitHub Actions as a serverless compute engine and Git as a flat-file database, providing automated multi-channel alerts without the need for traditional hosting.

## 🚀 System Architecture

This project eliminates the need for an always-on VPS or SQL database by leveraging CI/CD pipelines for daily execution and state mutation. 

*   **Zero-Cost Compute:** Scheduled cron jobs via GitHub Actions execute Python notification logic twice daily.
*   **Flat-File State Management:** `tasks.json` and `timetable.json` act as the primary data stores. State changes (adding/completing tasks) are automatically committed back to the repository via GitHub Actions.
*   **Mobile-First Dispatch:** Utilizes GitHub `workflow_dispatch` inputs to create a pseudo-frontend within the GitHub Mobile app, allowing for on-the-go task management.
*   **Temporal Logic & Lookahead:** Handles UTC to IST time-delta conversions, deduplicates warnings by ID, and executes weekend-specific lookahead logic (Friday evening previews for Monday morning).

## 🛠️ Tech Stack

*   **Language:** Python 3.10
*   **Orchestration:** GitHub Actions (Cron & Workflow Dispatch)
*   **Data Serialization:** JSON
*   **Protocols:** SMTP (SSL) with HTML injection
*   **Timezone Handling:** Python `zoneinfo`

## ⚙️ Features

*   **Smart E-Mail Briefings:** Generates an HTML-formatted daily briefing containing the current day's lecture schedule and faculty details.
*   **Multi-Tier Task Alerts:** Dynamically categorizes pending tasks into Urgent (Due Today), Advance Notice (Due Tomorrow), and Weekend Prep.
*   **Auto-Cleanup & ID Recycling:** Automatically purges completed tasks from the JSON datastore and recycles lowest-available IDs to prevent infinite file growth.
*   **Smart Search Completion:** Parses string inputs to mark tasks as complete either by integer ID or keyword matching.
*   **Regex Boundary Matching:** Ensures task abbreviations strictly match timetable subjects using word boundaries (`\b`) to prevent false-positive alerts.

## 📝 Setup & Deployment

1. **Clone the Repository:** 
   Clone this template to your personal GitHub account.
2. **Configure Environment Secrets:**
   Navigate to `Settings > Secrets and variables > Actions` and add the following:
   * `SENDER_EMAIL`: The Gmail address sending the alerts.
   * `SENDER_APP_PASSWORD`: A 16-character Google App Password.
   * `RECEIVER_EMAIL`: The destination email address.
3. **Populate Timetable:**
   Edit `timetable.json` with your weekly schedule following the provided schema.
4. **Enable GitHub Actions:**
   Navigate to the Actions tab and enable workflows. The system will now run autonomously based on the `.yml` cron schedules.

## 📱 Usage

Task management is handled entirely without code via the GitHub Mobile app or web interface:

1. Navigate to the **Actions** tab.
2. Select **📝 Add Pending Task**.
3. Choose the subject from the static dropdown and enter the task description.
4. The GitHub runner will dynamically assign an ID, mutate `tasks.json`, and commit the changes to the repository.
