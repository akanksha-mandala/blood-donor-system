# Blood Donor System

A full-stack web application designed to connect blood donors and recipients efficiently based on blood group and geographic proximity.

## Overview
The Blood Donor System allows donors and recipients to register separately.  
The system matches donors and recipients based on compatible blood groups and a configurable distance radius (up to 2000 km).

Once a match is found, both parties receive notification messages with relevant details.

## Key Features
- Separate interfaces for donors and recipients
- Dashboard displaying:
  - Total donors
  - Total recipients
  - Total requests
  - Successfully solved requests
- Blood group–based matching
- Location-based search with adjustable radius (up to 2000 km)
- SMS notifications using Twilio API
- Secure environment variable management
- Data persistence using MySQL

## Tech Stack
**Frontend**
- HTML
- CSS

**Backend**
- Python (Flask)

**Database**
- MySQL

**Third-Party Services**
- Twilio (SMS notifications)

## How It Works
1. Donors register through the donor interface.
2. Recipients submit blood requirements with location and blood group.
3. The system searches for compatible donors within the selected distance range.
4. If a match is found:
   - Donor receives recipient details via SMS.
   - Recipient receives donor details via SMS.
5. All donor and recipient data is stored securely in the database.

## Note on Twilio
The project uses Twilio for SMS notifications.  
The current implementation works with a free Twilio trial account, which may expire or have usage limits.

## Project Status
This project is currently a functional prototype and can be extended with:
- Authentication enhancements
- UI improvements
- Email notifications
- Deployment to cloud platforms

## Author
Akanksha Mandala
