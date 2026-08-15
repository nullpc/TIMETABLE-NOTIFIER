import json
import os
import sys

subject = os.getenv("SUBJECT")
task_desc = os.getenv("TASK_DESC")

if not subject or not task_desc:
    print("Error: Subject or Task Description missing from GitHub Actions inputs.")
    sys.exit(1)

filename = "tasks.json"

# Load existing tasks
try:
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            content = f.read().strip()
            tasks = json.loads(content) if content else []
    else:
        tasks = []
except Exception as e:
    print(f"Error loading {filename}: {e}")
    tasks = []

# --- THE HISTORY LOGIC (Max 100) ---
# If we have 100 or more tasks, we must delete the oldest COMPLETED task to make room.
if len(tasks) >= 100:
    # Find all completed tasks
    completed_tasks = [t for t in tasks if t.get("status") == "completed"]
    
    if completed_tasks:
        # Remove the oldest one (the first one in the list)
        oldest_completed = completed_tasks[0]
        tasks.remove(oldest_completed)
        print(f"🧹 History limit reached (100). Removed oldest completed task to make room (ID #{oldest_completed.get('id')}).")
    else:
        # If there are 100 tasks and ALL of them are pending, we have a problem!
        print("❌ Error: You have 100 PENDING tasks! Please complete some before adding more.")
        sys.exit(1)

# Find the lowest available ID between 1 and 100
used_ids = {t.get("id") for t in tasks}
next_id = 1
while next_id in used_ids:
    next_id += 1

# Create the new task
new_task = {
    "id": next_id,
    "subject": subject,
    "task": task_desc,
    "status": "pending"
}

tasks.append(new_task)

# Sort the file by ID so it looks neat when you read the JSON
tasks = sorted(tasks, key=lambda x: x.get("id", 100))

# Save it back to tasks.json
try:
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=4)
    print(f"✅ Successfully added Task #{next_id}: {subject} - {task_desc}")
except Exception as e:
    print(f"Error saving to {filename}: {e}")
    sys.exit(1)
