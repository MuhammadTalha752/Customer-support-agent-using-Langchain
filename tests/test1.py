"""
Run this directly: python test_step1.py
Paste the printed output back to Claude.
"""
from database import init_db, create_complaint, get_complaint_by_number, update_complaint_status
 
init_db()
print("DB initialized OK")
 
c = create_complaint(user_id="user_123", description="My delivery was 3 hours late")
print("Created complaint:", c.complaint_number, "| status:", c.status)
 
fetched = get_complaint_by_number(c.complaint_number)
print("Fetched back:", fetched.complaint_number, "| description:", fetched.description)
 
updated = update_complaint_status(c.complaint_number, "in_progress")
print("Updated status:", updated.status)
 