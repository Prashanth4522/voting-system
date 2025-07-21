# 🗳️ Voting System Using Facial Recognition

A secure, web-based voting system that uses **facial recognition** to verify voter identity. Built with Python, Flask, OpenCV, and face_recognition library, this project ensures a streamlined and fraud-proof voting process.

---

## 🚀 Features

- 🔐 **User Registration** with facial data, Aadhaar number & Voter ID
- 🧠 **Facial Recognition Login** using webcam
- ✅ **Age Verification** (18+ eligibility check)
- 🗳️ **Secure Voting Portal** for authenticated users
- 🧾 **Admin Dashboard** to add candidates, view results, and manage voters
- 📊 **Real-Time Vote Counting**
- 💻 Clean front-end with HTML/CSS

---

## 🛠️ Tech Stack

- **Frontend:** HTML, CSS
- **Backend:** Python, Flask
- **Face Recognition:** face_recognition, OpenCV
- **Database:** SQLite
- **Others:** dlib, PIL, NumPy

---

## 📂 Folder Structure

voting-system/
├── app.py
├── face_recognition.py
├── templates/
│ ├── login.html
│ ├── register.html
│ ├── face_verify.html
│ ├── vote.html
│ ├── result.html
│ └── admin_dashboard.html
├── static/
│ └── css/
│ └── style.css
├── database/
│ └── voting_system.db
├── requirements.txt
└── README.md



Create Virtual Environment
python -m venv venv
venv\Scripts\activate   # Windows
# OR
source venv/bin/activate  # macOS/Linux


Install Dependencies
bash
Copy
Edit

Run the Application

bash
Copy
Edit
python app.py
pip install -r requirements.txt

Open browser and visit:
👉 http://localhost:5000


