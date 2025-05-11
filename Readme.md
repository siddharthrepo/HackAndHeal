# 🩺 Chikitsa360 – Telemedicine & Consultation Platform

Chikitsa360 is a full-stack Django-based telemedicine web application enabling patients and doctors to interact via real-time video consultations, with post-call transcripts, secure authentication, and integrated payment processing.

## 🚀 Features

- 👨‍⚕️ Doctor and patient authentication system
- 📅 Book and manage appointments in dynamic time slots
- 📹 One-on-one video consultations (Daily.co + WebRTC)
- 🧾 Automatic call transcript generation using Deepgram
- 💳 Payment integration via Razorpay (In Progress)
- 📨 Email notifications for appointments and transcripts
- 🔒 Secure login with email-based custom auth backend
- 📂 Admin panel to manage users, doctors, and services
- ⚙️ Channels + ASGI for real-time communication support
- 🖼️ Static & media file support for profile images and documents

---

## 🧩 Tech Stack

- **Backend:** Django, Django Channels, PostgreSQL
- **Frontend:** HTML, CSS, JS, WebRTC
- **WebSockets:** Channels, ASGI
- **Video API:** [Daily.co](https://www.daily.co/)
- **Transcription API:** [Deepgram](https://deepgram.com/)
- **Payments:** [Razorpay](https://razorpay.com/) (In Progress)
- **Email:** SMTP (Gmail)
- **Deployment-ready:** Koyeb

---

## ⚙️ Setup Instructions

### 1. Clone the Repo

```bash
git clone https://github.com/yourusername/chikitsa360.git
cd chikitsa360

2.Create Virtual Environment
python -m venv venv
source venv/bin/activate

3.Install Requirements
pip install -r requirements.txt

4. Set Up .env
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
OPENAI_API_KEY=your-openai-api-key

5.  Apply Migrations
python manage.py makemigrations
python manage.py migrate

6.Create Superuser
python manage.py createsuperuser

7.Run Server
python manage.py runserver


 Security Notes
Do not run with DEBUG=True in production.

Set up proper ALLOWED_HOSTS in production.

Use HTTPS and reverse proxy (e.g., Nginx) for deployment.

Set SESSION_COOKIE_SECURE, CSRF_COOKIE_SECURE, and SECURE_SSL_REDIRECT to True in production.

🙌 Author
Siddharth Raturi


MIT License

Copyright (c) 2025 Siddharth Raturi

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES, OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
