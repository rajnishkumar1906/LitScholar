# 📚 LitScholar – AI-Powered Virtual Librarian

LitScholar is a modern, full-stack microservices application that transforms book discovery into a conversational experience. Using **Retrieval-Augmented Generation (RAG)** and **Semantic Search**, it allows users to find books using natural language and receive AI-driven recommendations.

---

## 🚀 Key Features

- **Conversational Discovery**: Ask "I want a book like Interstellar but with more focus on biology" and get reasoned results with citations
- **Semantic Search**: Powered by sentence-transformers and ChromaDB for deep contextual relevance
- **Microservices Architecture**: Decoupled backend services for maximum scalability
- **Personalized Dashboard**: "For You" recommendations based on your viewing history
- **Integrated Email**: Identity service handles welcome emails and login alerts directly via SMTP
- **AI Librarian Chat**: Context-aware conversations about books with follow-up questions
- **Google OAuth**: Seamless authentication with Google accounts
- **Splash screen**: Session-scoped welcome overlay on first load (matches global background & glass UI)

---

## 🔐 Authentication & Identity (cookies + microservices)

- The **identity service** (formerly auth-service) sets **httpOnly** cookies (`access_token`, `refresh_token`) on login, register, token refresh, and Google OAuth (redirect returns with `Set-Cookie`, no tokens in the URL).
- The **identity service** also handles all **Email notifications** (SMTP) for user lifecycle events (welcome, login alerts, password resets).
- The **React app** calls the identity API with **`credentials: included`** / Axios **`withCredentials: true`** so the browser sends cookies automatically.
- Other services (e.g. **RAG** on a different port) do not receive auth cookies cross-origin. The client stores the access JWT **in memory only** (from JSON responses) for **`Authorization: Bearer`** to those APIs—**not** in `localStorage`. Logout clears memory and hits **`POST /auth/logout`** to invalidate the refresh token server-side.

---

## 🛠️ Tech Stack

### **Frontend**
- React 18 + Vite
- Tailwind CSS with Glassmorphism
- React Router v6
- Axios with interceptors
- React Toastify

### **Backend**
- FastAPI (Python 3.13+)
- Neon PostgreSQL (Serverless)
- ChromaDB (Vector Database)
- Google Gemini API
- JWT with HTTP-only cookies
- SMTP integration (Integrated into Identity Service)

---

## 🏗️ High-Level Architecture

```
┌────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                  │
│                                                                            │
│                       ┌─────────────────────────┐                          │
│                       │     React Frontend      │                          │
│                       │     (Port 5173)         │                          │
│                       │  - Tailwind CSS         │                          │
│                       │  - React Router         │                          │
│                       │  - Axios interceptors   │                          │
│                       └────────────┬────────────┘                          │
│                                    │                                       │
│                                    ▼                                       │
└────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ HTTP/JSON
                                    │
┌───────────────────────────────────────────────────────────────────────────┐
│                            MICROSERVICES LAYER                            │
│                                                                           │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │                                                                    │   │
│  │  ┌──────────────┐    ┌──────────────┐                              │   │
│  │  │   Identity   │    │     RAG      │                              │   │
│  │  │   Service    │    │   Service    │                              │   │
│  │  │   :8000      │    │   :8001      │                              │   │
│  │  │              │    │              │                              │   │
│  │  │ • JWT Auth   │    │ • Gemini AI  │                              │   │
│  │  │ • Google OAuth│    │ • ChromaDB  │                              │   │
│  │  │ • Users      │    │ • Semantic   │                              │   │
│  │  │ • Email SMTP │    │   Search     │                              │   │
│  │  └──────┬───────┘    └──────┬───────┘                              │   │
│  │         │                   │                                      │   │
│  │         └───────────────────┼───────────────────┘                  │   │
│  │                             │                                      │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                   │                                       │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Data Flow Diagram

```
┌──────────┐    1. Login/Register     ┌──────────┐    2. Verify     ┌──────────┐
│  React   │ ───────────────────────> │ Identity │ ───────────────> │  Neon    │
│  Frontend│ <─────────────────────── │  Service │ <─────────────── │   DB     │
└──────────┘    7. JWT + Cookies      └──────────┘    3. User Data  └──────────┘
      │                                    
      │ 4. Search Books                    ┌──────────┐    5. Query     ┌──────────┐
      └──────────────────────────────────> │   RAG    │ ─────────────>  │ ChromaDB │
                                           │  Service │ <─────────────  │          │
      ┌──────────────────────────────────< │          │    6. Embeddings└──────────┘
      │ 8. Results + AI Response           └──────────┘
```

---

## 📊 Service Communication Matrix

| Service | Talks To | Purpose |
|---------|----------|---------|
| **Frontend** | All Services | User interface & API calls |
| **Identity** | NeonDB, Google OAuth, SMTP | Auth, user data, & emails |
| **RAG** | NeonDB, ChromaDB, Gemini | Book search & AI responses |

---

## ⚙️ Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Neon DB Account
- Gemini API Key

### One-Line Setup
```bash
git clone https://github.com/rajnishk71249/litscholar.git
cd litscholar

# Create and activate global virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install all dependencies
pip install -r identity-service/requirements.txt -r rag-service/requirements.txt

# Start all services (requires 2 backend terminals)
cd identity-service && ..\venv\Scripts\python.exe run.py
cd rag-service && ..\venv\Scripts\python.exe run.py

# Start frontend
cd client && npm install && npm run dev
```

Visit `http://localhost:5173` 🚀

---

## 🌟 Why LitScholar?

✅ **Modern Architecture** - Microservices with FastAPI  
✅ **Production Ready** - JWT, cookies, webhooks, rate limiting  
✅ **AI-Powered** - Gemini API with RAG architecture  
✅ **Scalable** - Serverless DB, stateless services  
✅ **Beautiful UI** - Glassmorphism, smooth animations  

---

## 📁 Project Structure

```
LitScholar/
├── client/           # React + Vite (splash, dashboard, book detail)
├── identity-service/ # JWT, httpOnly cookies, OAuth, users, Email SMTP
├── rag-service/      # AI, Chroma, books API
└── data_processing/  # Embedding pipeline (optional)
```
