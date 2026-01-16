from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text  # <-- add this
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)

try:
    with app.app_context():
        result = db.session.execute(text("SELECT 1"))  # wrap SQL in text()
        print("✅ DB connection successful!", result.fetchone())
except Exception as e:
    print("❌ DB connection failed:", e)
