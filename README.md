# 🏥 **Chikitsa360** | *Healthcare Anywhere, Anytime*

<div align="center">
  <img src="static/images/chikitsa360-logo.png" alt="Chikitsa360 Banner" />
  <br/>
  <h3>🥇 Veersa Hackathon 2026 Submission | Use Case 2: Telehealth Solution</h3>
  <h4>Team: HackAndHeal- ABES College Batch of 2026</h4>
  
  [![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
  [![WebRTC](https://img.shields.io/badge/WebRTC-333333?style=for-the-badge&logo=webrtc&logoColor=white)](https://webrtc.org/)
  [![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
  [![Daily.co](https://img.shields.io/badge/Daily.co-5039FC?style=for-the-badge&logo=daily&logoColor=white)](https://www.daily.co/)
  [![Deepgram](https://img.shields.io/badge/Deepgram-2C0746?style=for-the-badge&logo=deepgram&logoColor=white)](https://deepgram.com/)
</div>

## 📋 **Project Overview**

**Chikitsa360** is a comprehensive telehealth platform addressing the post-pandemic need for accessible, quality healthcare from anywhere. Built with Django and modern web technologies, our solution enables seamless virtual consultations between patients and healthcare providers with the security, convenience, and effectiveness of in-person visits.

> *"Quality healthcare shouldn't be limited by geography. Chikitsa360 bridges the gap between patients and doctors, ensuring everyone has access to medical expertise regardless of location."*

<div align="center">
  <img src="/api/placeholder/700/400" alt="Chikitsa360 Dashboard Preview" />
</div>

## 🌟 **Key Features**

### 👥 **User Experience**
- **Intuitive Patient Portal** - Simple registration, medical history submission, and appointment booking
- **Doctor Directory** - Search and filter doctors by specialty, availability, and languages spoken
- **Smart Scheduling** - AI-powered appointment recommendations based on doctor availability and urgency
- **Virtual Waiting Room** - Real-time updates on appointment status and estimated wait times
- **Post-Consultation Summary** - Automated visit summaries with prescriptions and follow-up instructions

### 🩺 **Clinical Features**
- **HD Video Consultations** - Crystal-clear WebRTC-powered video encounters
- **Multi-participant Sessions** - Invite family members or specialists to join consultations
- **Live Transcription** - Real-time conversation transcription using Deepgram API
- **Screen Sharing** - Share test results, imaging, or educational materials
- **Digital Prescription** - E-prescriptions sent directly to patient's preferred pharmacy
- **Medical Records** - Secure storage and sharing of patient documents

### 🔒 **Security & Compliance**
- **End-to-End Encryption** - Secure video and messaging communications
- **PHI Protection** - HIPAA-compliant data storage and transmission
- **Role-Based Access** - Granular permissions system for healthcare team members
- **Audit Logging** - Comprehensive activity tracking for compliance purposes

### 💳 **Payment & Billing**
- **Transparent Pricing** - Clear fee structures displayed before booking
- **Multiple Payment Options** - Credit/debit cards, digital wallets, and insurance processing
- **Automated Receipts** - Instant payment confirmations and tax documentation
- **Insurance Verification** - Real-time benefits eligibility checking (in development)

## 🔍 **Technical Implementation**

### Architecture
```
Chikitsa360/
├── accounts/          # User authentication & profiles
├── appointments/      # Appointment scheduling & management
├── consultation/      # Video consultation & transcription
├── payments/          # Payment processing & billing
├── notifications/     # Email & SMS alerts
├── static/            # CSS, JavaScript, images
├── templates/         # HTML templates
└── chikitsa360/       # Project settings
```

### Technology Stack
- **Backend**: Django, Django Channels, PostgreSQL
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **WebSockets**: Django Channels, ASGI for real-time features
- **Video API**: Daily.co for WebRTC implementation
- **Transcription**: Deepgram for real-time speech-to-text
- **Payments**: Razorpay integration (in progress)
- **Email**: SMTP integration for notifications
- **Deployment**: Docker, Koyeb-ready

## 🚀 **Installation & Setup**

### Prerequisites
- Python 3.9+
- PostgreSQL
- API keys for Daily.co, Deepgram, and Razorpay

### Quick Start
1. **Clone the repository**
   ```bash
   git clone https://github.com/siddharthrepo/HackAndHeal.git
   cd HackAndHeal
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   Create a `.env` file with the following:
   ```
   SECRET_KEY=your-secret-key
   DEBUG=True
   PGDATABASE=chikitsa360
   PGUSER=postgres
   PGPASSWORD=your-password
   PGHOST=localhost
   PGPORT=5432
   RAZORPAY_KEY_ID=your-razorpay-key
   RAZORPAY_KEY_SECRET=your-razorpay-secret
   DAILY_API_KEY=your-daily-api-key
   DEEPGRAM_API_KEY=your-deepgram-api-key
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Start development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   Open your browser and navigate to `http://127.0.0.1:8000`

## 📊 **Use Case Implementation**

Our solution directly addresses the Veersa Hackathon Use Case 2 requirements:

1. ✅ **Instant access to health consultation** - Implemented through our intuitive user flow from registration to video consultation

2. ✅ **Patient information capture** - Comprehensive intake forms with specialty selection and medical history

3. ✅ **Integrated payment system** - Secure payment processing before consultation using Razorpay 

4. ✅ **Privacy protection for PHI data** - End-to-end encryption and secure storage of all patient data

5. ✅ **In-app chat and information sharing** - Real-time messaging during consultation sessions

6. ✅ **Transcription service for accent challenges** - Deepgram API integration for accurate transcription across accents and dialects

## 📱 **Live Demo**

- **Live Application**: [https://chikitsa360.koyeb.app](https://chikitsa360.koyeb.app)
- **Demo Video**: [Watch Project Demo](https://drive.google.com/file/d/1wqVfEuVkxP7hajtmYi1CWqQKUJ5nacaR/view?usp=sharing) <!-- 👈 Add your demo video link here -->
- **Demo Credentials**:
  - Patient: `patient@demo.com` / `patient123`
  - Doctor: `doctor@demo.com` / `doctor123`
  - Admin: `admin@demo.com` / `admin123`

## 🖼️ **UI/UX Design**

- **Figma Design**: [View Figma Prototype](https://www.figma.com/design/3yNxgww0xoN4VcDLo6QY2X/home-2?node-id=0-1&t=JJlQkXj3MgVOuFPB-1) <!-- 👈 Add your Figma link here -->
- **Design System**: Our interface follows Material Design principles with a custom healthcare-focused color palette
- **Accessibility**: WCAG 2.1 AA compliant with full keyboard navigation support

## 🏛️ **Information Architecture**

Our platform follows a user-centered information architecture designed for intuitive navigation:

```
Chikitsa360
├── Public Area
│   ├── Home Page
│   ├── Doctor Directory
│   ├── Specialties
│   ├── How It Works
│   ├── Pricing
│   ├── FAQs
│   ├── About Us
│   ├── Contact
│   ├── Blog
│   ├── Login
│   └── Register
│
├── Patient Portal
│   ├── Dashboard
│   ├── My Profile
│   │   ├── Personal Information
│   │   ├── Medical History
│   │   └── Insurance Details
│   ├── Appointments
│   │   ├── Upcoming
│   │   ├── Past
│   │   └── Book New
│   ├── Consultations
│   │   ├── Join Video Call
│   │   ├── Chat History
│   │   └── Transcripts
│   ├── Medical Records
│   ├── Prescriptions
│   ├── Billing & Payments
│   └── Help & Support
│
├── Doctor Portal
│   ├── Dashboard
│   ├── My Profile
│   │   ├── Professional Details
│   │   ├── Schedule Management
│   │   └── Account Settings
│   ├── Patient Management
│   ├── Appointments
│   │   ├── Today's Schedule
│   │   ├── Upcoming
│   │   └── Past
│   ├── Consultations
│   │   ├── Start Video Call
│   │   └── Patient History
│   ├── Prescriptions & Notes
│   └── Earnings & Reports
│
└── Admin Panel
    ├── User Management
    ├── Doctor Verification
    ├── Specialty Management
    ├── Appointment Overview
    ├── Payment Processing
    ├── System Logs
    └── Settings
```

The architecture ensures that users can quickly locate needed information with minimal clicks, following a logical flow from registration through consultation and follow-up care.

## 🧪 **Testing**

### Automated Tests
```bash
# Run all tests
python manage.py test

# Run specific test modules
python manage.py test accounts
python manage.py test consultation
```

### API Testing
We've included Postman collections for API testing in the `/docs` directory.

## 🔮 **Future Enhancements**

- **AI-Powered Symptom Assessment** - Pre-consultation symptom checking
- **IoT Integration** - Support for connected medical devices
- **Multilingual Support** - Interface translation and real-time interpretation
- **Mobile Applications** - Native iOS and Android apps
- **Pharmacy Integration** - Direct prescription fulfillment partnerships

## 👨‍💻 **Team Members**

- **Siddharth Raturi** - Full Stack Development & Project Lead
- **Stuti Sharma** - UI/UX Design & Frontend Implementation
- **Sona Poddar** - Backend Development & API Integration
- **Vidhi Jain** - Testing & Quality Assurance

## 📜 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">
  <p>Made with ❤️ for the Veersa Hackathon 2026</p>
  <p>© 2025 Team Code Healers | ABES College Batch of 2026</p>
</div>
