import sys
from database import SessionLocal
from models import DBUser

db = SessionLocal()
users = db.query(DBUser).all()
print("Usuarios:")
for u in users:
    print(f"- {u.username} (rol: {u.role})")
db.close()
