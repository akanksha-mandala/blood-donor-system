from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_migrate import Migrate
from flask_mail import Mail, Message
from models import db, Donor, Recipient, EmergencyRequest, is_eligible_for_donation
from config import Config
from twilio.rest import Client
import random
from datetime import date, timedelta
import os
import math  # For distance calculation

# ----------------------------
# Mock City Coordinates
# ----------------------------
MOCK_CITY_COORDS = {
    "New York": (40.7128, -74.0060),
    "Los Angeles": (34.0522, -118.2437),
    "London": (51.5074, 0.1278),
    "KLU": (16.4402, 80.6120),
    "Hyderabad": (17.3850, 78.4867),
    "Mumbai": (19.0760, 72.8777)
}


def get_coords_from_city(city: str) -> tuple[float, float]:
    coords = MOCK_CITY_COORDS.get(city.title(), None)
    if coords:
        return coords
    return (random.uniform(10, 50), random.uniform(70, 100))


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate the great-circle distance (in km) between two coordinates."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2 +
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
        math.sin(dlon / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))
    return R * c


def find_potential_donors(request_data: EmergencyRequest):
    compatible_groups = {
        "O-": ["O-"],
        "O+": ["O+", "O-"],
        "A-": ["A-", "O-"],
        "A+": ["A+", "A-", "O+", "O-"],
        "B-": ["B-", "O-"],
        "B+": ["B+", "B-", "O+", "O-"],
        "AB-": ["AB-", "A-", "B-", "O-"],
        "AB+": ["AB+", "AB-", "A+", "A-", "B+", "B-", "O+", "O-"]
    }.get(request_data.blood_group_needed.upper(), [])

    potential_donors = Donor.query.filter(
        Donor.blood_group.in_(compatible_groups),
        Donor.available == True,
    ).all()

    nearby_donors = []
    for donor in potential_donors:
        if donor.latitude and donor.longitude:
            distance = haversine_distance(
                donor.latitude,
                donor.longitude,
                request_data.latitude,
                request_data.longitude
            )
            if distance <= request_data.radius_km:
                nearby_donors.append(donor)

    eligible_donors = [d for d in nearby_donors if d.is_eligible]
    return eligible_donors


def send_notification(donor: Donor, request_data: EmergencyRequest):
    try:
        message_body = (
            f"🚨 Blood Needed!\n"
            f"{request_data.blood_group_needed} required for {request_data.recipient.full_name} "
            f"in {request_data.city}.\n"
            f"Contact hospital: {request_data.hospital_name or 'Unknown'}."
        )
        message = twilio_client.messages.create(
            body=message_body,
            from_=app.config['TWILIO_PHONE_NUMBER'],
            to=f"+91{donor.phone}"
        )
        print(f"✅ SMS sent to {donor.full_name}: SID {message.sid}")
    except Exception as e:
        print(f"❌ Failed to send SMS to {donor.full_name}: {str(e)}")


# ----------------------------
# ✅ Flask App Setup (Fixed)
# ----------------------------
app = Flask(__name__, template_folder='../frontend', static_folder='../frontend/static')
app.config.from_object(Config)

db.init_app(app)
migrate = Migrate(app, db)
CORS(app)
mail = Mail(app)

twilio_client = Client(app.config['TWILIO_ACCOUNT_SID'], app.config['TWILIO_AUTH_TOKEN'])

with app.app_context():
    db.create_all()

# ----------------------------
# API Routes
# ----------------------------
@app.route('/api/stats')
def stats():
    total_donors = Donor.query.count()
    active_requests = EmergencyRequest.query.filter_by(status='active').count()
    resolved_cases = EmergencyRequest.query.filter_by(status='resolved').count()
    total_recipients = Recipient.query.count()

    return jsonify({
        'total_donors': total_donors,
        'active_requests': active_requests,
        'resolved_cases': resolved_cases,
        'total_recipients': total_recipients
    })


@app.route('/api/donors/register', methods=['POST'])
def register_donor():
    data = request.json
    city = data.get('city')
    latitude, longitude = get_coords_from_city(city)

    existing_donor = Donor.query.filter(
        (Donor.email == data['email']) | (Donor.phone == data['phone'])
    ).first()
    if existing_donor:
        return jsonify({"message": "Donor already registered with this email or phone."}), 409

    try:
        new_donor = Donor(
            full_name=data['full_name'],
            age=data['age'],
            email=data['email'],
            phone=data['phone'],
            blood_group=data['blood_group'].upper(),
            city=city,
            latitude=latitude,
            longitude=longitude,
            last_donation=None
        )
        db.session.add(new_donor)
        db.session.commit()
        return jsonify({"message": "Donor registered successfully!", "donor_id": new_donor.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Error registering donor: {str(e)}"}), 500

@app.route('/api/recipients/register', methods=['POST'])
def register_recipient():
    data = request.json
    city = data.get('city')
    hospital_name = data.get('hospital_name', 'Unknown')
    radius_km = data.get('radius_km', 2000)

    latitude, longitude = get_coords_from_city(city)

    try:
        # --- Save new recipient ---
        new_recipient = Recipient(
            full_name=data['full_name'],
            phone=data['phone'],
            email=data['email'],
            blood_group_needed=data['blood_group_needed'].upper(),
            city=city,
            latitude=latitude,
            longitude=longitude
        )
        db.session.add(new_recipient)
        db.session.flush()

        # --- Create emergency request ---
        new_request = EmergencyRequest(
            recipient_id=new_recipient.id,
            blood_group_needed=new_recipient.blood_group_needed,
            city=new_recipient.city,
            latitude=new_recipient.latitude,
            longitude=new_recipient.longitude,
            hospital_name=hospital_name,
            radius_km=radius_km,
            fulfilled=False
        )
        db.session.add(new_request)
        db.session.commit()

        # --- Find potential donors ---
        potential_donors = find_potential_donors(new_request)

        # --- Notify recipient ---
        if potential_donors:
            donor_names = ", ".join([d.full_name for d in potential_donors])
            donor_contacts = ", ".join([d.phone for d in potential_donors])
            recipient_msg = (
                f"Hey {new_recipient.full_name}, we found {len(potential_donors)} matching donors nearby! "
                f"Donors: {donor_names}. Contacts: {donor_contacts}. ❤️"
            )
            twilio_client.messages.create(
                body=recipient_msg,
                from_=app.config['TWILIO_PHONE_NUMBER'],
                to=f"+91{new_recipient.phone}"
            )

            # ✅ Notify each donor too
            for donor in potential_donors:
                try:
                    donor_msg = (
                        f"🚨 URGENT: {new_recipient.full_name} in {city} needs {new_recipient.blood_group_needed} blood!\n"
                        f"Hospital: {hospital_name}\n"
                        f"Contact: {new_recipient.phone}"
                    )
                    twilio_client.messages.create(
                        body=donor_msg,
                        from_=app.config['TWILIO_PHONE_NUMBER'],
                        to=f"+91{donor.phone}"
                    )
                    print(f"✅ Notified donor {donor.full_name}")
                except Exception as e:
                    print(f"❌ Failed to notify donor {donor.full_name}: {str(e)}")

        else:
            # No donors found
            twilio_client.messages.create(
                body=f"Sorry {new_recipient.full_name}, no matching donors were found nearby yet. We’ll notify you as soon as possible.",
                from_=app.config['TWILIO_PHONE_NUMBER'],
                to=f'+91{new_recipient.phone}'
            )

        return jsonify({
            "message": "Recipient registered successfully and donors notified.",
            "request_id": new_request.id,
            "donors_notified": len(potential_donors)
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"Error during recipient registration: {e}")
        return jsonify({"message": f"Error registering recipient or creating request: {str(e)}"}), 500

    except Exception as e:
        db.session.rollback()
        print(f"Error during recipient registration: {e}")
        return jsonify({"message": f"Error registering recipient or creating request: {str(e)}"}), 500


@app.route('/api/requests', methods=['GET'])
def get_recent_requests():
    requests = EmergencyRequest.query.filter_by(fulfilled=False).order_by(EmergencyRequest.timestamp.desc()).limit(5).all()
    requests_list = [r.to_dict() for r in requests]

    if not requests_list:
        requests_list = [
            {"id": 998, "full_name": "Ravi Kumar", "blood_group_needed": "O-", "city": "Mumbai", "hospital_name": "City General", "radius_km": 10, "timestamp": date.today().strftime("%Y-%m-%d %H:%M:%S"), "fulfilled": False},
            {"id": 999, "full_name": "Sita Devi", "blood_group_needed": "B+", "city": "Hyderabad", "hospital_name": "Apollo Clinic", "radius_km": 5, "timestamp": date.today().strftime("%Y-%m-%d %H:%M:%S"), "fulfilled": False},
        ]

    return jsonify(requests_list)


# ----------------------------
# Serve Frontend Files
# ----------------------------
@app.route('/')
def serve_frontend():
    return send_from_directory(os.path.join(os.path.dirname(__file__), '../frontend'), 'index.html')


@app.route('/<path:path>')
def serve_static_files(path):
    frontend_folder = os.path.join(os.path.dirname(__file__), '../frontend')
    return send_from_directory(frontend_folder, path)


# ----------------------------
# Run Server
# ----------------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
