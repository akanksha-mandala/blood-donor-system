from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date

db = SQLAlchemy()

VERIFICATION_PENDING = "pending"
VERIFICATION_VERIFIED = "verified"
VERIFICATION_REJECTED = "rejected"
VERIFICATION_BLOCKED = "blocked"

REQUEST_PENDING = "pending_verification"
REQUEST_VERIFIED = "verified"
REQUEST_REJECTED = "rejected"
REQUEST_COMPLETED = "completed"

MATCH_PENDING = "pending"
MATCH_ACCEPTED = "accepted"
MATCH_DECLINED = "declined"
MATCH_ARRIVED = "arrived_at_hospital"
MATCH_COMPLETED = "completed"


def is_eligible_for_donation(last_donation: date) -> bool:
    if last_donation:
        return (date.today() - last_donation).days >= 90
    return True


class Donor(db.Model):
    __tablename__ = "donors"

    id = db.Column(db.Integer, primary_key=True)

    full_name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    phone = db.Column(db.String(20), nullable=False, unique=True)
    blood_group = db.Column(db.String(5), nullable=False)
    city = db.Column(db.String(50), nullable=False)

    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)

    aadhaar_number = db.Column(db.String(12), nullable=False, unique=True)
    aadhaar_masked = db.Column(db.String(20), nullable=False)
    aadhaar_verified = db.Column(db.Boolean, default=False)

    profile_image = db.Column(db.String(255), nullable=True)
    aadhaar_proof_file = db.Column(db.String(255), nullable=True)
    verification_source = db.Column(db.String(50), default="manual_review")

    verification_status = db.Column(db.String(20), default=VERIFICATION_PENDING)
    verified_badge = db.Column(db.Boolean, default=False)
    is_blocked = db.Column(db.Boolean, default=False)

    available = db.Column(db.Boolean, default=True)
    donation_count = db.Column(db.Integer, default=0)
    last_donation = db.Column(db.Date, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    verified_at = db.Column(db.DateTime, nullable=True)

    matches = db.relationship("DonationMatch", backref="donor", lazy=True)

    @property
    def is_eligible(self):
        return is_eligible_for_donation(self.last_donation)

    def to_dict(self):
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
            "aadhaar_masked": self.aadhaar_masked,
            "aadhaar_verified": self.aadhaar_verified,
            "profile_image": self.profile_image,
            "aadhaar_proof_file": self.aadhaar_proof_file,
            "verification_source": self.verification_source,
            "verification_status": self.verification_status,
            "verified_badge": self.verified_badge,
            "is_blocked": self.is_blocked,
            "available": self.available,
            "donation_count": self.donation_count,
            "last_donation": self.last_donation.strftime("%Y-%m-%d") if self.last_donation else None,
            "is_eligible": self.is_eligible,
        }


class Recipient(db.Model):
    __tablename__ = "recipients"

    id = db.Column(db.Integer, primary_key=True)

    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False, unique=True)
    email = db.Column(db.String(100), nullable=False)
    blood_group_needed = db.Column(db.String(5), nullable=False)
    city = db.Column(db.String(50), nullable=False)

    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)

    aadhaar_number = db.Column(db.String(12), nullable=False, unique=True)
    aadhaar_masked = db.Column(db.String(20), nullable=False)
    aadhaar_verified = db.Column(db.Boolean, default=False)

    profile_image = db.Column(db.String(255), nullable=True)
    aadhaar_proof_file = db.Column(db.String(255), nullable=True)
    verification_source = db.Column(db.String(50), default="manual_review")

    verification_status = db.Column(db.String(20), default=VERIFICATION_PENDING)
    is_blocked = db.Column(db.Boolean, default=False)
    scam_flag = db.Column(db.Boolean, default=False)

    hospital_name = db.Column(db.String(100), nullable=True)
    hospital_address = db.Column(db.String(255), nullable=True)
    doctor_name = db.Column(db.String(100), nullable=True)
    attender_name = db.Column(db.String(100), nullable=True)
    attender_phone = db.Column(db.String(20), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    verified_at = db.Column(db.DateTime, nullable=True)

    requests = db.relationship("EmergencyRequest", backref="recipient", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "full_name": self.full_name,
            "phone": self.phone,
            "email": self.email,
            "blood_group_needed": self.blood_group_needed,
            "city": self.city,
            "aadhaar_masked": self.aadhaar_masked,
            "aadhaar_verified": self.aadhaar_verified,
            "profile_image": self.profile_image,
            "aadhaar_proof_file": self.aadhaar_proof_file,
            "verification_source": self.verification_source,
            "verification_status": self.verification_status,
            "is_blocked": self.is_blocked,
            "scam_flag": self.scam_flag,
            "hospital_name": self.hospital_name,
            "hospital_address": self.hospital_address,
            "doctor_name": self.doctor_name,
            "attender_name": self.attender_name,
            "attender_phone": self.attender_phone,
        }


class EmergencyRequest(db.Model):
    __tablename__ = "emergency_requests"

    id = db.Column(db.Integer, primary_key=True)

    recipient_id = db.Column(db.Integer, db.ForeignKey("recipients.id"), nullable=False)

    blood_group_needed = db.Column(db.String(5), nullable=False)
    city = db.Column(db.String(50), nullable=False)

    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)

    hospital_name = db.Column(db.String(100), nullable=True)
    hospital_address = db.Column(db.String(255), nullable=True)
    doctor_name = db.Column(db.String(100), nullable=True)
    attender_name = db.Column(db.String(100), nullable=True)
    attender_phone = db.Column(db.String(20), nullable=True)

    radius_km = db.Column(db.Integer, default=5)

    verification_status = db.Column(db.String(30), default=REQUEST_PENDING)
    donation_status = db.Column(db.String(30), default="not_started")

    fulfilled = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default="active")

    verified_by = db.Column(db.String(100), nullable=True)
    verified_at = db.Column(db.DateTime, nullable=True)

    admin_notes = db.Column(db.Text, nullable=True)

    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    matches = db.relationship("DonationMatch", backref="request", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "recipient_id": self.recipient_id,
            "recipient_name": self.recipient.full_name,
            "blood_group_needed": self.blood_group_needed,
            "city": self.city,
            "hospital_name": self.hospital_name,
            "hospital_address": self.hospital_address,
            "doctor_name": self.doctor_name,
            "attender_name": self.attender_name,
            "attender_phone": self.attender_phone,
            "radius_km": self.radius_km,
            "verification_status": self.verification_status,
            "donation_status": self.donation_status,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        }


class DonationMatch(db.Model):
    __tablename__ = "donation_matches"

    id = db.Column(db.Integer, primary_key=True)

    request_id = db.Column(db.Integer, db.ForeignKey("emergency_requests.id"), nullable=False)
    donor_id = db.Column(db.Integer, db.ForeignKey("donors.id"), nullable=False)

    status = db.Column(db.String(30), default=MATCH_PENDING)

    accepted_at = db.Column(db.DateTime, nullable=True)
    arrived_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class VerificationLog(db.Model):
    __tablename__ = "verification_logs"

    id = db.Column(db.Integer, primary_key=True)

    user_type = db.Column(db.String(20), nullable=False)
    user_id = db.Column(db.Integer, nullable=False)

    action = db.Column(db.String(50), nullable=False)
    result = db.Column(db.String(20), nullable=False)

    notes = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)