import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from restrack.auth.auth import validate_password

print("Testing auth module...")
result = validate_password("admin", "admin")
print(f"Auth result for admin/admin: {result}")
