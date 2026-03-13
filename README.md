# Blood Donor Management and Emergency Verification System

A full-stack web application for real-time blood donor discovery, emergency blood request handling, identity verification, and hospital-safe donor-recipient coordination.

---

## Project Overview

This system is designed to reduce delays in emergency blood access by connecting verified donors and verified recipients using blood compatibility, geographic radius filtering, and secure approval workflows.

Unlike basic donor directories, this platform introduces a structured trust layer:

- donor verification
- recipient verification
- Aadhaar proof upload
- admin approval
- hospital-based donation coordination
- fraud control workflow

The system ensures that blood requests are processed only after verification and that donor-recipient interaction follows safer controlled conditions.

---

## Core Problem Addressed

In emergency situations, locating a compatible blood donor quickly remains difficult because conventional methods depend heavily on manual phone calls, social media forwarding, and unreliable donor lists.

Major issues in traditional systems include:

- delayed donor identification  
- lack of donor authenticity  
- fake emergency requests  
- repeated misuse of donor data  
- unsafe direct contact between strangers  

This project addresses these gaps through automated matching and controlled verification.

---

## Major Features

### Donor Module

- donor registration
- blood group selection
- city and geolocation capture
- availability status
- Aadhaar number submission
- Aadhaar proof upload
- donor profile image upload
- donor verification status
- verified donor badge
- donation count tracking
- last donation status

---

### Recipient Module

- emergency blood request creation
- blood group requirement
- radius-based donor search
- hospital name
- hospital address
- doctor name
- attender details
- Aadhaar submission
- Aadhaar proof upload
- profile image upload
- verification workflow

---

### Smart Matching Engine

The platform matches donors using:

- compatible blood group logic
- latitude / longitude distance calculation
- configurable radius in kilometers

This ensures that only medically compatible nearby donors are contacted.

---

### Verification and Safety Layer

The platform includes trust enforcement:

- Aadhaar masked display
- document-based verification
- admin approval / rejection
- scam flag support
- blocked account handling

---

### Admin Dashboard

Separate verification dashboards are available for:

- donor verification
- recipient verification
- active verified requests
- fraud / blocked accounts

Admin can:

- verify
- reject
- block
- approve emergency requests
- resend donor notifications

---

### Hospital-Safe Donation Flow

To improve safety:

- donor phone is hidden until approval
- recipient phone is hidden until approval
- hospital location becomes default meeting point
- donation request completion is tracked

---

### SMS Notification System

SMS alerts are integrated using Twilio.

When a verified request is approved:

- compatible donors receive emergency alerts
- hospital details are included
- recipient receives donor availability updates

---

## Technology Stack

## Frontend

- HTML  
- CSS  
- JavaScript  

---

## Backend

- Python  
- Flask  

---

## Database

- MySQL  

---

## Third-Party Integration

- Twilio SMS API  

---

## Database Design

Main entities:

- donors  
- recipients  
- emergency_requests  

Additional verification fields include:

- aadhaar number  
- masked aadhaar  
- profile image  
- proof file  
- verification source  
- verification timestamps  

---

## Current Advanced Functionalities

- radius search up to selected km
- blood compatibility filtering
- verified donor cards
- admin-controlled request approval
- document upload system
- resend notification logic
- donor trust scoring foundation

---

## Future Scope

Possible production extensions:

- official government identity API integration
- hospital-side approval login
- QR-based donor verification
- OTP-based identity confirmation
- cloud deployment
- live ambulance integration
- multilingual support

---

## Research Relevance

This project belongs to:

- Healthcare Technology  
- Emergency Response Systems  
- Real-Time Location Intelligence  
- Verification-Centered Web Systems  

---

## Author

**Akanksha Mandala**

---

## Project Type

Academic Full Stack Prototype with Real-Time Emergency Workflow
