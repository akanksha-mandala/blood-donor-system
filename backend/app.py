from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_migrate import Migrate
from flask_mail import Mail
from werkzeug.utils import secure_filename
from models import db, Donor, Recipient, EmergencyRequest
from config import Config
from twilio.rest import Client
from datetime import datetime
import random
import os
import math
import re
import uuid

# ----------------------------
# Mock City Coordinates
# ----------------------------
MOCK_CITY_COORDS = {
    "New York": (40.7128, -74.0060),
    "Los Angeles": (34.0522, -118.2437),
    "London": (51.5074, 0.1278),
    "KLU": (16.4402, 80.6120),
    "Hyderabad": (17.3850, 78.4867),
    "Mumbai": (19.0760, 72.8777),
    "Chennai": (13.0827, 80.2707),
    "Bangalore": (12.9716, 77.5946),
    "Delhi": (28.6139, 77.2090),
    "Krishnankoil": (9.4499, 77.7979),
    "Vijayawada": (16.5062, 80.6480),
}

# ----------------------------
# Flask App Setup
# ----------------------------
app = Flask(__name__, template_folder='../frontend', static_folder='../frontend/static')
app.config.from_object(Config)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
DONOR_PROFILE_FOLDER = os.path.join(UPLOAD_FOLDER, 'donor_profiles')
DONOR_AADHAAR_FOLDER = os.path.join(UPLOAD_FOLDER, 'donor_aadhaar')
RECIPIENT_PROFILE_FOLDER = os.path.join(UPLOAD_FOLDER, 'recipient_profiles')
RECIPIENT_AADHAAR_FOLDER = os.path.join(UPLOAD_FOLDER, 'recipient_aadhaar')

for folder in [
    UPLOAD_FOLDER,
    DONOR_PROFILE_FOLDER,
    DONOR_AADHAAR_FOLDER,
    RECIPIENT_PROFILE_FOLDER,
    RECIPIENT_AADHAAR_FOLDER
]:
    os.makedirs(folder, exist_ok=True)

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
ALLOWED_DOC_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'pdf'}

db.init_app(app)
migrate = Migrate(app, db)
CORS(app)
mail = Mail(app)

twilio_client = Client(app.config['TWILIO_ACCOUNT_SID'], app.config['TWILIO_AUTH_TOKEN'])

# ----------------------------
# Utility Functions
# ----------------------------
def get_coords_from_city(city: str) -> tuple[float, float]:
    coords = MOCK_CITY_COORDS.get((city or "").title(), None)
    if coords:
        return coords
    return (random.uniform(10, 30), random.uniform(70, 90))


def haversine_distance(lat1, lon1, lat2, lon2):
    if None in [lat1, lon1, lat2, lon2]:
        return float("inf")

    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))
    return R * c


def validate_indian_phone(phone: str) -> bool:
    phone = str(phone).strip()
    return bool(re.fullmatch(r"[6-9]\d{9}", phone))


def validate_aadhaar(aadhaar: str) -> bool:
    aadhaar = str(aadhaar).strip().replace(" ", "")
    return bool(re.fullmatch(r"\d{12}", aadhaar))


def mask_aadhaar(aadhaar: str) -> str:
    aadhaar = str(aadhaar).strip().replace(" ", "")
    if len(aadhaar) == 12:
        return f"XXXX-XXXX-{aadhaar[-4:]}"
    return "XXXX-XXXX-XXXX"


def format_indian_sms_number(phone: str) -> str:
    phone = str(phone).strip()
    if phone.startswith("+91"):
        return phone
    return f"+91{phone}"


def send_sms(to_number: str, message_body: str) -> bool:
    try:
        twilio_client.messages.create(
            body=message_body,
            from_=app.config['TWILIO_PHONE_NUMBER'],
            to=to_number
        )
        return True
    except Exception as e:
        print(f"❌ SMS failed to {to_number}: {e}")
        return False


def get_compatible_groups(required_group: str):
    return {
        "O-": ["O-"],
        "O+": ["O+", "O-"],
        "A-": ["A-", "O-"],
        "A+": ["A+", "A-", "O+", "O-"],
        "B-": ["B-", "O-"],
        "B+": ["B+", "B-", "O+", "O-"],
        "AB-": ["AB-", "A-", "B-", "O-"],
        "AB+": ["AB+", "AB-", "A+", "A-", "B+", "B-", "O+", "O-"]
    }.get((required_group or "").upper(), [])


def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def save_uploaded_file(file_obj, target_folder, allowed_extensions):
    if not file_obj or not file_obj.filename:
        return None

    if not allowed_file(file_obj.filename, allowed_extensions):
        raise ValueError("Invalid file type uploaded.")

    ext = file_obj.filename.rsplit('.', 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    safe_name = secure_filename(unique_name)
    save_path = os.path.join(target_folder, safe_name)
    file_obj.save(save_path)

    rel_folder = os.path.relpath(target_folder, UPLOAD_FOLDER).replace("\\", "/")
    return f"{rel_folder}/{safe_name}"


def find_verified_matching_donors(request_data: EmergencyRequest):
    compatible_groups = get_compatible_groups(request_data.blood_group_needed)
    print(f"[DEBUG] Compatible groups for request {request_data.id}: {compatible_groups}")

    potential_donors = Donor.query.filter(
        Donor.blood_group.in_(compatible_groups),
        Donor.available == True,
        Donor.verification_status == "verified",
        Donor.is_blocked == False
    ).all()

    print(f"[DEBUG] Potential donors found: {[d.id for d in potential_donors]}")

    nearby_donors = []
    for donor in potential_donors:
        if donor.latitude is not None and donor.longitude is not None:
            distance = haversine_distance(
                donor.latitude,
                donor.longitude,
                request_data.latitude,
                request_data.longitude
            )
            print(
                f"[DEBUG] Donor {donor.id} | blood={donor.blood_group} | "
                f"available={donor.available} | verified={donor.verification_status} | "
                f"coords=({donor.latitude},{donor.longitude}) | "
                f"request_coords=({request_data.latitude},{request_data.longitude}) | "
                f"distance={distance:.2f} km | radius={request_data.radius_km} | "
                f"eligible={donor.is_eligible}"
            )

            if distance <= request_data.radius_km and donor.is_eligible:
                nearby_donors.append(donor)

    print(f"[DEBUG] Nearby matched donors: {[d.id for d in nearby_donors]}")
    return nearby_donors


def notify_verified_donors_for_request(emergency_request: EmergencyRequest):
    donors = find_verified_matching_donors(emergency_request)

    print(f"[DEBUG] Notifying donors for request {emergency_request.id}: {[d.id for d in donors]}")

    for donor in donors:
        donor_msg = (
            f"Blood Group Needed: {emergency_request.blood_group_needed}\n"
            f"Hospital: {emergency_request.hospital_name or 'Not Provided'}\n"
            f"Address: {emergency_request.hospital_address or emergency_request.city}\n"
            f"Please visit the hospital directly if you can donate."
        )

        print(f"[DEBUG] Sending SMS to donor {donor.id} at {donor.phone}")
        ok = send_sms(format_indian_sms_number(donor.phone), donor_msg)
        print(f"[DEBUG] SMS send result for donor {donor.id}: {ok}")

    return donors


# ----------------------------
# Upload Serving
# ----------------------------
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


# ----------------------------
# API Routes
# ----------------------------
@app.route('/api/stats', methods=['GET'])
def stats():
    total_donors = Donor.query.count()
    verified_donors = Donor.query.filter_by(verification_status='verified').count()
    pending_donors = Donor.query.filter_by(verification_status='pending').count()

    total_recipients = Recipient.query.count()
    pending_requests = EmergencyRequest.query.filter_by(verification_status='pending').count()
    verified_requests = EmergencyRequest.query.filter_by(
        verification_status='verified',
        status='active'
    ).count()
    resolved_cases = EmergencyRequest.query.filter_by(status='resolved').count()

    return jsonify({
        'total_donors': total_donors,
        'verified_donors': verified_donors,
        'pending_donors': pending_donors,
        'total_recipients': total_recipients,
        'pending_requests': pending_requests,
        'verified_requests': verified_requests,
        'resolved_cases': resolved_cases
    })


# ----------------------------
# Donor Registration
# ----------------------------
@app.route('/api/donors/register', methods=['POST'])
def register_donor():
    data = request.form

    full_name = data.get('full_name', '').strip()
    age = data.get('age')
    email = data.get('email', '').strip().lower()
    phone = str(data.get('phone', '')).strip()
    blood_group = data.get('blood_group', '').upper().strip()
    city = data.get('city', '').strip()
    aadhaar_number = str(data.get('aadhaar_number', '')).replace(" ", "").strip()

    profile_image_file = request.files.get('profile_image')
    aadhaar_proof_file = request.files.get('aadhaar_proof_file')

    if not all([full_name, age, email, phone, blood_group, city, aadhaar_number]):
        return jsonify({"message": "All donor fields are required."}), 400

    if not validate_indian_phone(phone):
        return jsonify({"message": "Enter a valid 10-digit Indian phone number."}), 400

    if not validate_aadhaar(aadhaar_number):
        return jsonify({"message": "Enter a valid 12-digit Aadhaar number."}), 400

    if not profile_image_file or not aadhaar_proof_file:
        return jsonify({"message": "Profile image and Aadhaar proof are required."}), 400

    latitude, longitude = get_coords_from_city(city)

    existing_donor = Donor.query.filter(
        (Donor.email == email) |
        (Donor.phone == phone) |
        (Donor.aadhaar_number == aadhaar_number)
    ).first()

    if existing_donor:
        return jsonify({"message": "A donor already exists with this email, phone, or Aadhaar number."}), 409

    try:
        profile_image_path = save_uploaded_file(
            profile_image_file,
            DONOR_PROFILE_FOLDER,
            ALLOWED_IMAGE_EXTENSIONS
        )
        aadhaar_proof_path = save_uploaded_file(
            aadhaar_proof_file,
            DONOR_AADHAAR_FOLDER,
            ALLOWED_DOC_EXTENSIONS
        )

        new_donor = Donor(
            full_name=full_name,
            age=age,
            email=email,
            phone=phone,
            blood_group=blood_group,
            city=city,
            latitude=latitude,
            longitude=longitude,
            last_donation=None,
            available=True,
            aadhaar_number=aadhaar_number,
            aadhaar_masked=mask_aadhaar(aadhaar_number),
            aadhaar_verified=False,
            profile_image=profile_image_path,
            aadhaar_proof_file=aadhaar_proof_path,
            verification_source='document_upload',
            verification_status='pending',
            verified_badge=False,
            is_blocked=False,
            donation_count=0,
            created_at=datetime.utcnow()
        )

        db.session.add(new_donor)
        db.session.commit()

        return jsonify({
            "message": "Donor registered successfully. Verification is pending admin approval.",
            "donor_id": new_donor.id,
            "verification_status": new_donor.verification_status,
            "verified_badge": new_donor.verified_badge
        }), 201

    except ValueError as ve:
        return jsonify({"message": str(ve)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Error registering donor: {str(e)}"}), 500


# ----------------------------
# Recipient Registration
# ----------------------------
@app.route('/api/recipients/register', methods=['POST'])
def register_recipient():
    data = request.form

    full_name = data.get('full_name', '').strip()
    phone = str(data.get('phone', '')).strip()
    email = data.get('email', '').strip().lower()
    blood_group_needed = data.get('blood_group_needed', '').upper().strip()
    city = data.get('city', '').strip()
    aadhaar_number = str(data.get('aadhaar_number', '')).replace(" ", "").strip()
    hospital_name = data.get('hospital_name', 'Unknown').strip()
    hospital_address = data.get('hospital_address', '').strip()
    doctor_name = data.get('doctor_name', '').strip()
    attender_name = data.get('attender_name', '').strip()
    attender_phone = str(data.get('attender_phone', '')).strip()
    radius_km = int(data.get('radius_km', 20))

    profile_image_file = request.files.get('profile_image')
    aadhaar_proof_file = request.files.get('aadhaar_proof_file')

    if not all([
        full_name, phone, email, blood_group_needed, city,
        aadhaar_number, hospital_name, hospital_address,
        doctor_name, attender_name, attender_phone
    ]):
        return jsonify({"message": "All recipient and hospital verification fields are required."}), 400

    if not validate_indian_phone(phone):
        return jsonify({"message": "Enter a valid recipient phone number."}), 400

    if not validate_indian_phone(attender_phone):
        return jsonify({"message": "Enter a valid attender phone number."}), 400

    if not validate_aadhaar(aadhaar_number):
        return jsonify({"message": "Enter a valid 12-digit Aadhaar number."}), 400

    if not profile_image_file or not aadhaar_proof_file:
        return jsonify({"message": "Profile image and Aadhaar proof are required."}), 400

    latitude, longitude = get_coords_from_city(city)

    existing_recipient = Recipient.query.filter(
        (Recipient.email == email) |
        (Recipient.phone == phone) |
        (Recipient.aadhaar_number == aadhaar_number)
    ).first()

    if existing_recipient:
        return jsonify({"message": "A recipient already exists with this email, phone, or Aadhaar number."}), 409

    try:
        profile_image_path = save_uploaded_file(
            profile_image_file,
            RECIPIENT_PROFILE_FOLDER,
            ALLOWED_IMAGE_EXTENSIONS
        )
        aadhaar_proof_path = save_uploaded_file(
            aadhaar_proof_file,
            RECIPIENT_AADHAAR_FOLDER,
            ALLOWED_DOC_EXTENSIONS
        )

        new_recipient = Recipient(
            full_name=full_name,
            phone=phone,
            email=email,
            blood_group_needed=blood_group_needed,
            city=city,
            latitude=latitude,
            longitude=longitude,
            aadhaar_number=aadhaar_number,
            aadhaar_masked=mask_aadhaar(aadhaar_number),
            aadhaar_verified=False,
            profile_image=profile_image_path,
            aadhaar_proof_file=aadhaar_proof_path,
            verification_source='document_upload',
            verification_status='pending',
            is_blocked=False,
            scam_flag=False,
            hospital_name=hospital_name,
            hospital_address=hospital_address,
            doctor_name=doctor_name,
            attender_name=attender_name,
            attender_phone=attender_phone,
            created_at=datetime.utcnow()
        )
        db.session.add(new_recipient)
        db.session.flush()

        new_request = EmergencyRequest(
            recipient_id=new_recipient.id,
            blood_group_needed=blood_group_needed,
            city=city,
            latitude=latitude,
            longitude=longitude,
            hospital_name=hospital_name,
            hospital_address=hospital_address,
            doctor_name=doctor_name,
            attender_name=attender_name,
            attender_phone=attender_phone,
            radius_km=radius_km,
            fulfilled=False,
            status='active',
            verification_status='pending',
            donation_status='awaiting_verification',
            admin_notes=None
        )
        db.session.add(new_request)
        db.session.commit()

        send_sms(
            format_indian_sms_number(new_recipient.phone),
            (
                f"Your blood request has been submitted successfully.\n"
                f"Request ID: {new_request.id}\n"
                f"Status: Pending Verification\n"
                f"Our team will verify your identity and hospital details before notifying donors."
            )
        )

        return jsonify({
            "message": "Recipient registered successfully. Request is pending verification.",
            "recipient_id": new_recipient.id,
            "request_id": new_request.id,
            "verification_status": "pending"
        }), 201

    except ValueError as ve:
        return jsonify({"message": str(ve)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Error registering recipient or creating request: {str(e)}"}), 500


# ----------------------------
# Requests Feed - only verified active requests
# ----------------------------
@app.route('/api/requests', methods=['GET'])
def get_recent_requests():
    requests = EmergencyRequest.query.filter_by(
        fulfilled=False,
        verification_status='verified',
        status='active'
    ).order_by(EmergencyRequest.timestamp.desc()).limit(5).all()

    return jsonify([r.to_dict() for r in requests])


# ----------------------------
# Verified Donors List
# ----------------------------
@app.route('/api/donors/verified-list', methods=['GET'])
def verified_donors_list():
    donors = Donor.query.filter_by(
        verification_status='verified',
        verified_badge=True,
        is_blocked=False
    ).order_by(Donor.donation_count.desc(), Donor.id.desc()).limit(12).all()

    return jsonify([
        {
            "id": donor.id,
            "full_name": donor.full_name,
            "blood_group": donor.blood_group,
            "city": donor.city,
            "donation_count": donor.donation_count or 0,
            "verified_badge": donor.verified_badge,
            "profile_image": f"/uploads/{donor.profile_image}" if donor.profile_image else None
        }
        for donor in donors
    ])


# ----------------------------
# Admin Dashboards
# ----------------------------
@app.route('/api/admin/donors/pending', methods=['GET'])
def admin_pending_donors():
    donors = Donor.query.filter_by(verification_status='pending').order_by(Donor.id.desc()).all()
    return jsonify([d.to_dict() for d in donors])


@app.route('/api/admin/recipients/pending', methods=['GET'])
def admin_pending_recipients():
    recipients = Recipient.query.filter_by(verification_status='pending').order_by(Recipient.id.desc()).all()
    return jsonify([r.to_dict() for r in recipients])


@app.route('/api/admin/requests/pending', methods=['GET'])
def admin_pending_requests():
    requests = EmergencyRequest.query.filter_by(verification_status='pending').order_by(EmergencyRequest.id.desc()).all()
    return jsonify([r.to_dict() for r in requests])

@app.route('/api/admin/requests/<int:request_id>/resend', methods=['POST'])
def admin_resend_request_notifications(request_id):
    emergency_request = EmergencyRequest.query.get_or_404(request_id)

    if emergency_request.verification_status != 'verified':
        return jsonify({"message": "Only verified requests can resend notifications."}), 400

    matched_donors = notify_verified_donors_for_request(emergency_request)

    return jsonify({
        "message": "Donor notifications resent.",
        "request_id": emergency_request.id,
        "donors_notified": len(matched_donors)
    })


@app.route('/api/admin/fraud-blocked', methods=['GET'])
def admin_fraud_blocked():
    blocked_donors = Donor.query.filter_by(is_blocked=True).all()
    blocked_recipients = Recipient.query.filter(
        (Recipient.is_blocked == True) | (Recipient.scam_flag == True)
    ).all()

    return jsonify({
        "blocked_donors": [d.to_dict() for d in blocked_donors],
        "blocked_recipients": [r.to_dict() for r in blocked_recipients]
    })


# ----------------------------
# Admin Actions - Donor
# ----------------------------
@app.route('/api/admin/donors/<int:donor_id>/verify', methods=['POST'])
def admin_verify_donor(donor_id):
    donor = Donor.query.get_or_404(donor_id)

    if donor.is_blocked:
        return jsonify({"message": "Blocked donor cannot be verified."}), 400

    try:
        donor.aadhaar_verified = True
        donor.verification_status = 'verified'
        donor.verified_badge = True
        donor.verified_at = datetime.utcnow()

        db.session.commit()
        return jsonify({"message": "Donor verified successfully.", "verified_badge": True})

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Error verifying donor: {str(e)}"}), 500


@app.route('/api/admin/donors/<int:donor_id>/reject', methods=['POST'])
def admin_reject_donor(donor_id):
    donor = Donor.query.get_or_404(donor_id)

    try:
        donor.verification_status = 'rejected'
        donor.verified_badge = False
        donor.available = False
        db.session.commit()
        return jsonify({"message": "Donor rejected successfully."})

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Error rejecting donor: {str(e)}"}), 500


@app.route('/api/admin/donors/<int:donor_id>/block', methods=['POST'])
def admin_block_donor(donor_id):
    donor = Donor.query.get_or_404(donor_id)

    try:
        donor.is_blocked = True
        donor.available = False
        donor.verification_status = 'blocked'
        donor.verified_badge = False
        db.session.commit()
        return jsonify({"message": "Donor blocked successfully."})

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Error blocking donor: {str(e)}"}), 500


# ----------------------------
# Admin Actions - Recipient
# ----------------------------
@app.route('/api/admin/recipients/<int:recipient_id>/verify', methods=['POST'])
def admin_verify_recipient(recipient_id):
    recipient = Recipient.query.get_or_404(recipient_id)

    if recipient.is_blocked or recipient.scam_flag:
        return jsonify({"message": "Blocked or flagged recipient cannot be verified."}), 400

    try:
        recipient.aadhaar_verified = True
        recipient.verification_status = 'verified'
        recipient.verified_at = datetime.utcnow()
        db.session.commit()
        return jsonify({"message": "Recipient verified successfully."})

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Error verifying recipient: {str(e)}"}), 500


@app.route('/api/admin/recipients/<int:recipient_id>/reject', methods=['POST'])
def admin_reject_recipient(recipient_id):
    recipient = Recipient.query.get_or_404(recipient_id)

    try:
        recipient.verification_status = 'rejected'
        db.session.commit()
        return jsonify({"message": "Recipient rejected successfully."})

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Error rejecting recipient: {str(e)}"}), 500


@app.route('/api/admin/recipients/<int:recipient_id>/flag-scam', methods=['POST'])
def admin_flag_recipient_scam(recipient_id):
    recipient = Recipient.query.get_or_404(recipient_id)

    try:
        recipient.scam_flag = True
        recipient.is_blocked = True
        recipient.verification_status = 'blocked'
        db.session.commit()
        return jsonify({"message": "Recipient flagged as scam and blocked successfully."})

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Error flagging recipient: {str(e)}"}), 500


# ----------------------------
# Admin Actions - Request
# ----------------------------
@app.route('/api/admin/requests/<int:request_id>/verify', methods=['POST'])
def admin_verify_request(request_id):
    emergency_request = EmergencyRequest.query.get_or_404(request_id)
    recipient = Recipient.query.get(emergency_request.recipient_id)

    if not recipient:
        return jsonify({"message": "Recipient not found for this request."}), 404

    if recipient.verification_status != 'verified':
        return jsonify({"message": "Verify recipient before verifying request."}), 400

    try:
        emergency_request.verification_status = 'verified'
        emergency_request.donation_status = 'awaiting_donor_acceptance'
        emergency_request.verified_at = datetime.utcnow()
        emergency_request.verified_by = 'admin'
        db.session.commit()

        matched_donors = notify_verified_donors_for_request(emergency_request)

        send_sms(
            format_indian_sms_number(recipient.phone),
            (
                f"Your blood request #{emergency_request.id} has been VERIFIED.\n"
                f"{len(matched_donors)} verified donors have been notified.\n"
                f"Please proceed only through the hospital."
            )
        )

        return jsonify({
            "message": "Request verified and matching donors notified.",
            "request_id": emergency_request.id,
            "donors_notified": len(matched_donors)
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Error verifying request: {str(e)}"}), 500


@app.route('/api/admin/requests/<int:request_id>/reject', methods=['POST'])
def admin_reject_request(request_id):
    emergency_request = EmergencyRequest.query.get_or_404(request_id)

    try:
        emergency_request.verification_status = 'rejected'
        emergency_request.donation_status = 'rejected'
        emergency_request.status = 'rejected'
        db.session.commit()
        return jsonify({"message": "Request rejected successfully."})

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Error rejecting request: {str(e)}"}), 500


@app.route('/api/admin/requests/<int:request_id>/complete', methods=['POST'])
def admin_complete_request(request_id):
    emergency_request = EmergencyRequest.query.get_or_404(request_id)

    try:
        emergency_request.fulfilled = True
        emergency_request.status = 'resolved'
        emergency_request.donation_status = 'completed'
        db.session.commit()
        return jsonify({"message": "Request marked as completed successfully."})

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Error completing request: {str(e)}"}), 500


# ----------------------------
# Donor Accept Request
# ----------------------------
@app.route('/api/donors/<int:donor_id>/accept-request/<int:request_id>', methods=['POST'])
def donor_accept_request(donor_id, request_id):
    donor = Donor.query.get_or_404(donor_id)
    emergency_request = EmergencyRequest.query.get_or_404(request_id)
    recipient = Recipient.query.get(emergency_request.recipient_id)

    if donor.verification_status != 'verified' or donor.is_blocked:
        return jsonify({"message": "Only verified donors can accept requests."}), 403

    if emergency_request.verification_status != 'verified':
        return jsonify({"message": "This request is not verified yet."}), 400

    try:
        emergency_request.assigned_donor_id = donor.id
        emergency_request.donation_status = 'donor_accepted'

        donor.available = False
        donor.donation_count = (donor.donation_count or 0) + 1

        db.session.commit()

        if recipient:
            send_sms(
                format_indian_sms_number(recipient.phone),
                (
                    f"A verified donor has accepted your request #{emergency_request.id}.\n"
                    f"Please reach the hospital: {emergency_request.hospital_name}\n"
                    f"Address: {emergency_request.hospital_address or emergency_request.city}"
                )
            )

        return jsonify({
            "message": "Request accepted successfully. Please donate only at the hospital.",
            "request_id": emergency_request.id,
            "hospital_name": emergency_request.hospital_name,
            "hospital_address": emergency_request.hospital_address
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Error accepting request: {str(e)}"}), 500


# ----------------------------
# Verified Requests for Donor Dashboard
# ----------------------------
@app.route('/api/donors/verified-requests', methods=['GET'])
def donor_verified_requests():
    requests = EmergencyRequest.query.filter_by(
        verification_status='verified',
        status='active',
        fulfilled=False
    ).order_by(EmergencyRequest.timestamp.desc()).all()

    response = []
    for req in requests:
        response.append({
            "id": req.id,
            "blood_group_needed": req.blood_group_needed,
            "city": req.city,
            "hospital_name": req.hospital_name,
            "hospital_address": req.hospital_address,
            "doctor_name": req.doctor_name,
            "radius_km": req.radius_km,
            "verification_status": req.verification_status,
            "donation_status": req.donation_status,
            "timestamp": req.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        })

    return jsonify(response)


# ----------------------------
# Serve Frontend Files
# ----------------------------
@app.route('/')
def serve_frontend():
    return send_from_directory(
        os.path.join(os.path.dirname(__file__), '../frontend'),
        'index.html'
    )


@app.route('/<path:path>')
def serve_static_files(path):
    frontend_folder = os.path.join(os.path.dirname(__file__), '../frontend')
    return send_from_directory(frontend_folder, path)


# ----------------------------
# Run Server
# ----------------------------
if __name__ == '__main__':
    app.run(debug=True, port=5000)