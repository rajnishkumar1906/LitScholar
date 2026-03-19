# 📚 LitScholar – AI-Powered Virtual Librarian

LitScholar is a modern, full-stack microservices application that transforms book discovery into a conversational experience. Using **Retrieval-Augmented Generation (RAG)** and **Semantic Search**, it allows users to find books using natural language and receive AI-driven recommendations.

---

## 🚀 Key Features

- **Conversational Discovery**: Ask "I want a book like Interstellar but with more focus on biology" and get reasoned results with citations
- **Semantic Search**: Powered by sentence-transformers and ChromaDB for deep contextual relevance
- **Microservices Architecture**: Four decoupled backend services for maximum scalability
- **Personalized Dashboard**: "For You" recommendations based on your viewing history
- **Real Email Notifications**: Welcome emails, login alerts, and payment confirmations
- **Premium Tier**: Razorpay integration for monthly/yearly/lifetime subscriptions
- **AI Librarian Chat**: Context-aware conversations about books with follow-up questions
- **Google OAuth**: Seamless authentication with Google accounts

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
- Razorpay SDK
- SMTP integration

---

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                    │
│                                                                             │
│                       ┌─────────────────────────┐                          │
│                       │     React Frontend      │                          │
│                       │     (Port 5173)         │                          │
│                       │  - Tailwind CSS         │                          │
│                       │  - React Router         │                          │
│                       │  - Axios interceptors   │                          │
│                       └────────────┬────────────┘                          │
│                                    │                                        │
│                                    ▼                                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ HTTP/JSON
                                    │
┌─────────────────────────────────────────────────────────────────────────────┐
│                            MICROSERVICES LAYER                               │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │   │
│  │  │   Auth       │    │     RAG      │    │   Payment    │          │   │
│  │  │   Service    │    │   Service    │    │   Service    │          │   │
│  │  │   :8000      │    │   :8001      │    │   :8003      │          │   │
│  │  │              │    │              │    │              │          │   │
│  │  │ • JWT Auth   │    │ • Gemini AI  │    │ • Razorpay   │          │   │
│  │  │ • Google OAuth│    │ • ChromaDB  │    │ • Subscriptions│          │   │
│  │  │ • Users      │    │ • Semantic   │    │ • Plans      │          │   │
│  │  │              │    │   Search     │    │              │          │   │
│  │  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘          │   │
│  │         │                   │                   │                   │   │
│  │         └───────────────────┼───────────────────┘                   │   │
│  │                             │                                        │   │
│  │                    ┌────────▼────────┐                              │   │
│  │                    │   Email Service │                              │   │
│  │                    │     :8002       │                              │   │
│  │                    │                 │                              │   │
│  │                    │  • SMTP         │                              │   │
│  │                    │  • Templates    │                              │   │
│  │                    │  • Notifications│                              │   │
│  │                    └─────────────────┘                              │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
            ┌───────────────────────┼───────────────────────┐
            ▼                       ▼                       ▼
┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
│   EXTERNAL          │  │   EXTERNAL          │  │   EXTERNAL          │
│   SERVICES          │  │   SERVICES          │  │   SERVICES          │
│                     │  │                     │  │                     │
│  ┌───────────────┐  │  │  ┌───────────────┐  │  │  ┌───────────────┐  │
│  │    Google     │  │  │  │   Razorpay    │  │  │  │    Gmail      │  │
│  │    OAuth      │◀─┘  │  │   Gateway     │◀─┘  │  │    SMTP       │◀─┘
│  └───────────────┘     │  └───────────────┘     │  └───────────────┘
│                        │                        │
└────────────────────────┴────────────────────────┴─────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                             DATA LAYER                                       │
│                                                                             │
│                    ┌─────────────────────────┐                             │
│                    │     Neon PostgreSQL      │                             │
│                    │   (Serverless DB)        │                             │
│                    │  - users                 │                             │
│                    │  - subscriptions         │                             │
│                    │  - email_logs            │                             │
│                    │  - refresh_tokens        │                             │
│                    └────────────┬────────────┘                             │
│                                 │                                          │
│                    ┌────────────▼────────────┐                             │
│                    │        ChromaDB          │                             │
│                    │    (Vector Database)     │                             │
│                    │  - book embeddings       │                             │
│                    │  - semantic search       │                             │
│                    └─────────────────────────┘                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Data Flow Diagram

```
┌──────────┐    1. Login/Register    ┌──────────┐    2. Verify     ┌──────────┐
│  React   │ ───────────────────────> │  Auth    │ ───────────────> │  Neon    │
│  Frontend│ <─────────────────────── │  Service │ <─────────────── │   DB     │
└──────────┘    7. JWT + Cookies      └──────────┘    3. User Data  └──────────┘
      │                                    
      │ 4. Search Books                    ┌──────────┐    5. Query    ┌──────────┐
      └──────────────────────────────────> │   RAG    │ ─────────────> │ ChromaDB │
                                           │  Service │ <───────────── │          │
      ┌──────────────────────────────────< │          │    6. Embeddings└──────────┘
      │ 8. Results + AI Response           └──────────┘
      │
      │ 9. Upgrade to Premium              ┌──────────┐   10. Create   ┌──────────┐
      └──────────────────────────────────> │ Payment  │ ─────────────> │ Razorpay │
                                           │ Service  │ <───────────── │ Gateway  │
      ┌──────────────────────────────────< └──────────┘   11. Order ID └──────────┘
      │ 12. Payment Success
      │
      │                                   ┌──────────┐   13. Webhook   ┌──────────┐
      └──────────────────────────────────> │ Payment  │ <───────────── │ Razorpay │
                                           │ Service  │    Payment     │ Gateway  │
                                           └────┬─────┘    Confirmed   └──────────┘
                                                │
                                           ┌────▼─────┐   14. Update   ┌──────────┐
                                           │ Payment  │ ─────────────> │  Neon    │
                                           │ Service  │    Subscription│   DB     │
                                           └────┬─────┘ <───────────── └──────────┘
                                                │
                                           ┌────▼─────┐   15. Trigger  ┌──────────┐
                                           │  Email   │ ─────────────> │  SMTP    │
                                           │ Service  │    Confirmation│  Gmail   │
                                           └──────────┘ <───────────── └──────────┘
```

---

## 📊 Service Communication Matrix

| Service | Talks To | Purpose |
|---------|----------|---------|
| **Frontend** | All Services | User interface & API calls |
| **Auth** | NeonDB, Google OAuth | Authentication & user data |
| **RAG** | NeonDB, ChromaDB, Gemini | Book search & AI responses |
| **Payment** | NeonDB, Razorpay | Subscriptions & payments |
| **Email** | NeonDB, Gmail SMTP | Notifications & receipts |

---

## ⚙️ Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Neon DB Account
- Gemini API Key
- Razorpay Test Credentials

### One-Line Setup
```bash
git clone https://github.com/rajnishk71249/litscholar.git
cd litscholar

# Start all services (requires 4 terminals)
cd auth-service && python run.py
cd rag-service && python run.py
cd email-service && python run.py
cd payment-service && python run.py

# Start frontend
cd client && npm install && npm run dev
```

Visit `http://localhost:5173` 🚀

---

## 🌟 Why LitScholar?

✅ **Modern Architecture** - Microservices with FastAPI  
✅ **Production Ready** - JWT, cookies, webhooks, rate limiting  
✅ **Real Payments** - Razorpay integration with webhooks  
✅ **AI-Powered** - Gemini API with RAG architecture  
✅ **Scalable** - Serverless DB, stateless services  
✅ **Beautiful UI** - Glassmorphism, smooth animations  

---

## 📁 Project Structure

```
LitScholar/
├── client/           # React Frontend
├── auth-service/     # JWT, OAuth, Users
├── rag-service/      # AI, Search, Books
├── email-service/    # SMTP, Templates
├── payment-service/  # Razorpay, Subscriptions
└── data_processing/  # Embedding pipeline
```

