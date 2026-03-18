# 📚 LitScholar – AI-Powered Virtual Librarian

LitScholar is a modern, full-stack microservices application that transforms book discovery into a conversational experience. Using **Retrieval-Augmented Generation (RAG)** and **Semantic Search**, it allows users to find books using natural language, receive AI-driven explanations for recommendations, and manage their personal reading journey.

---

## 🚀 Key Features

- **Conversational Discovery**: Ask "I want a book like Interstellar but with more focus on biology" and get reasoned results.
- **Semantic Search**: Powered by `sentence-transformers` and `ChromaDB` for deep contextual relevance.
- **Microservices Architecture**: Four decoupled backend services (Auth, RAG, Email, Payment) for maximum scalability.
- **Personalized Dashboard**: "For You" recommendations based on your viewing history and preferences.
- **Reading Progress Tracking**: Mark books as finished, track your yearly goals, and view your reading streaks.
- **Premium Tier**: Mock subscription system to unlock advanced AI librarian features.

---

## 🛠️ Tech Stack

### **Frontend**
- **Framework**: React (Vite)
- **Styling**: Tailwind CSS (Glassmorphism & Premium Amber Theme)
- **State Management**: React Context API (Global App State)
- **Networking**: Axios with interceptors for cross-service auth.

### **Backend (Microservices)**
- **API Framework**: FastAPI (Python 3.13+)
- **Database (Relational)**: Neon PostgreSQL (Serverless)
- **Database (Vector)**: ChromaDB (Local/Server-side)
- **Async Driver**: `asyncpg` for non-blocking database operations.
- **LLM Engine**: Google Gemini API
- **Embeddings**: HuggingFace `all-MiniLM-L6-v2`
- **Auth**: JWT (JSON Web Tokens) with `HttpOnly` cookies.

---

## 🧱 System Architecture

```mermaid
graph TD
    Client[React Frontend] --> Gateway[Auth Service :8000]
    Client --> RAG[RAG Service :8001]
    Client --> Email[Email Service :8002]
    Client --> Payment[Payment Service :8003]
    RAG --> Chroma[(ChromaDB)]
    RAG --> Neon[(Neon PostgreSQL)]
    Auth --> Neon
    Email --> Neon
    Payment --> Neon
```

### Service Breakdown:
1.  **[Auth Service](file:///auth-service)**: Manages users, JWT tokens, and profiles.
2.  **[RAG Service](file:///rag-service)**: The "brain" — handles AI chat, book search, and vector embeddings.
3.  **[Email Service](file:///email-service)**: Handles transactional emails like welcome messages and logs.
4.  **[Payment Service](file:///payment-service)**: Manages mock subscriptions and plan statuses.

---

## ⚙️ Setup & Installation

### 1. Prerequisites
- Python 3.11+
- Node.js 18+
- Neon DB Connection String
- Gemini API Key

### 2. Environment Variables
Create a `.env` file in the root directory:

```env
# Relational DB
DB_URL_NEON=postgresql://user:pass@host/db?sslmode=require

# AI & Search
GEMINI_API_KEY=your_gemini_key
JWT_SECRET=your_jwt_secret
SESSION_SECRET_KEY=your_session_key

# Service URLs
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:5173
```

### 3. Run the Backend
You need to start all four services. It is recommended to use virtual environments:

```bash
# In 4 separate terminals:
cd auth-service && python run.py
cd rag-service && python run.py
cd email-service && python run.py
cd payment-service && python run.py
```

### 4. Run the Frontend
```bash
cd client
npm install
npm run dev
```

### 5. Data Ingestion (Initial Setup)
To populate the database and generate embeddings:
```bash
python -m data_processing.run_pipeline
```

---

## 📁 Project Structure

```
LitScholar/
├── client/             # Vite + React Frontend
├── auth-service/       # JWT, Profiles, User Management
├── rag-service/        # AI Librarian, ChromaDB, Gemini RAG
├── email-service/      # Background Email Notifications
├── payment-service/    # Subscriptions & Premium Plans
├── data_processing/    # CSV Cleaning & Embedding Scripts
└── data/               # Raw datasets (book_raw.csv)
```

---

## 🛡️ License & Acknowledgements
- **License**: MIT
- **Inspiration**: Built for book lovers who want a smarter way to browse.
- **Author**: Rajnish Kumar (@rajnishk71249)

© 2026 LitScholar - Modern AI Librarian.
