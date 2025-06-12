# 🧑‍🤝‍🧑 Social Network Backend

This is the backend of a full-stack social networking platform inspired by Facebook, built with **Django**, **Django REST Framework**, and **Django Channels**.

It provides RESTful APIs and real-time WebSocket functionality for features like posts, likes, comments, chat, and notifications.

---

## 🔗 Frontend Repository

👉 [https://github.com/Mmy2000/social-network-react](https://github.com/Mmy2000/social-network-react)  
👉 [Live Frontend](https://social-network-react-black.vercel.app/)

### 🔐 Test Login

- **Email**: `testuser@email.com`  
- **Password**: `test1234`

---

## 🛠 Tech Stack

- 🐍 Django 4+
- ⚙️ Django REST Framework
- 🌐 Django Channels (WebSocket support)
- 🧵 Redis (as a channel layer for real-time features)
- 🗃️ PostgreSQL (or SQLite for local testing)
- 📦 JWT Authentication (SimpleJWT)

---

## 🚀 Features

- 🔐 Register / Login / JWT Authentication
- 🧾 User Profiles & Avatar Uploads
- 📝 Post Creation, Editing, Deletion
- 💬 Comments & Likes
- ✉️ Real-Time Messaging (Chat)
- 🔔 Notifications (WebSocket)
- 🖼️ Media file support

---

## 📦 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/Mmy2000/social-book.git
cd social-book
python -m venv env
source env/bin/activate  # on Windows: env\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
