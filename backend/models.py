from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, timedelta

db = SQLAlchemy()

# Function to check if a donor is eligible (donated at least 90 days ago)
def is_eligible_for_donation(last_donation: date) -> bool:
    """Checks if the last donation date allows for a new donation."""
    if last_donation:
        return (date.today() - last_donation).days >= 90
    return True


class Donor(db.Model):
    """Database model for registered blood donors."""
    __tablename__ = "donors"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    phone = db.Column(db.String(20), nullable=False)
    blood_group = db.Column(db.String(5), nullable=False)
    city = db.Column(db.String(50), nullable=False)

    # Coordinates for geolocation matching
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)

    last_donation = db.Column(db.Date, nullable=True)
    available = db.Column(db.Boolean, default=True)

    @property
    def is_eligible(self):
        """Check eligibility based on last donation date."""
        return is_eligible_for_donation(self.last_donation)

    def to_dict(self):
        """Returns a dictionary representation of the donor."""
        return {
            "id": self.id,
            "full_name": self.full_name,
            "age": self.age,
            "email": self.email,
            "phone": self.phone,
            "blood_group": self.blood_group,
            "city": self.city,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "last_donation": self.last_donation.strftime("%Y-%m-%d") if self.last_donation else None,
            "available": self.available,
            "is_eligible": self.is_eligible
        }


class Recipient(db.Model):
    """Database model for people requesting blood."""
    __tablename__ = "recipients"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    blood_group_needed = db.Column(db.String(5), nullable=False)
    city = db.Column(db.String(50), nullable=False)

    # Coordinates for proximity search
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)

    def to_dict(self):
        """Returns a dictionary representation of the recipient."""
        return {
            "id": self.id,
            "full_name": self.full_name,
            "phone": self.phone,
            "email": self.email,
            "blood_group_needed": self.blood_group_needed,
            "city": self.city,
            "latitude": self.latitude,
            "longitude": self.longitude
        }


class EmergencyRequest(db.Model):
    """Database model for active blood requests."""
    __tablename__ = "emergency_requests"

    id = db.Column(db.Integer, primary_key=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey("recipients.id"), nullable=False)
    blood_group_needed = db.Column(db.String(5), nullable=False)
    city = db.Column(db.String(50), nullable=False)

    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    hospital_name = db.Column(db.String(100), nullable=True)
    radius_km = db.Column(db.Integer, default=5)

    timestamp = db.Column(db.DateTime, default=datetime.now)
    fulfilled = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default='active')  # 👈 add this line

    recipient = db.relationship("Recipient", backref="requests")

    def to_dict(self):
        """Returns a dictionary representation of the emergency request."""
        return {
            "id": self.id,
            "recipient_id": self.recipient_id,
            "recipient_name": self.recipient.full_name,
            "blood_group_needed": self.blood_group_needed,
            "city": self.city,
            "hospital_name": self.hospital_name,
            "radius_km": self.radius_km,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "fulfilled": self.fulfilled,
            "status": self.status  # 👈 include this here too
        }


    def to_dict(self):
        """Returns a dictionary representation of the emergency request."""
        return {
            "id": self.id,
            "recipient_id": self.recipient_id,
            "recipient_name": self.recipient.full_name,
            "blood_group_needed": self.blood_group_needed,
            "city": self.city,
            "hospital_name": self.hospital_name,
            "radius_km": self.radius_km,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "fulfilled": self.fulfilled
        }
import math

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance (in km) between two coordinates using the Haversine formula."""
    R = 6371  # Earth radius in km
    lat_diff = math.radians(lat2 - lat1)
    lon_diff = math.radians(lon2 - lon1)
    a = (math.sin(lat_diff / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(lon_diff / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c
