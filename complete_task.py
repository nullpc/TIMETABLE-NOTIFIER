import json
import os
import sys

# The input from GitHub Actions can now be an ID or a piece of text
search_query = os.getenv("TASK_QUERY", "").strip()

if not search_query:
    print("Error: No task ID or name provided.")
    sys.exit(1)

try:
    with open("tasks.json", "r", encoding="utf-8") as f:
        tasks = json.load(f)
except Exception as e:
    print(f"Error loading tasks.json: {e}")
    sys.exit(1)

task_found = False

# Try matching by ID first, then by substring in the task description
for t in tasks:
    if t.get("status") == "pending":
        # Check if the user typed an exact ID number
        if search_query.isdigit() and str(t.get("id")) == search_query:
            t["status"] = "completed"
            print(f"✅ Marked Task #{t['id']} ('{t['task']}') as completed!")
            task_found = True
            break
        # Check if the user typed a word that exists in the task name
        elif not search_query.isdigit() and search_query.lower() in t.get("task", "").lower():
            t["status"] = "completed"
            print(f"✅ Marked Task #{t['id']} ('{t['task']}') as completed!")
            task_found = True
            break

if not task_found:
    print(f"❌ Could not find a pending task matching '{search_query}'.")
    sys.exit(1)

# Save the updated tasks.json
with open("tasks.json", "w", encoding="utf-8") as f:
    json.dump(tasks, f, indent=4)
