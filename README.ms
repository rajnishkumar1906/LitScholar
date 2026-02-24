# 📚 LitScholar - AI-Powered Virtual Librarian

![LitScholar Logo](public/litscholar-icon.svg)

LitScholar is an intelligent virtual librarian that understands natural language queries and recommends books with human-like reasoning. It combines modern AI/ML techniques with a robust full-stack architecture to provide personalized book recommendations and scholarly insights.

## 🚀 Features

### Core Functionality
- **Natural Language Search**: Describe what you're looking for in plain English
- **Semantic Book Retrieval**: Finds relevant books using vector embeddings
- **AI-Powered Explanations**: Get librarian-style recommendations with citations
- **Follow-up Questions**: Ask detailed questions about specific books
- **User Authentication**: Email/password and Google OAuth support

### Technical Highlights
- **Offline-first Architecture**: Local LLM inference for privacy
- **Semantic Search**: SentenceTransformers + ChromaDB for high-precision retrieval
- **Citation System**: Every claim is traceable to source books
- **Responsive UI**: Beautiful amber/brown themed interface

## 🏗️ Architecture

### Frontend (React + Vite)
- **Pages**: Auth, Dashboard, BookDetail, Profile
- **Components**: Navbar, Footer, SearchBar, BookCard
- **State Management**: Context API (AppContext)
- **Styling**: Tailwind CSS with custom amber/brown theme
- **Icons**: React Icons + Custom SVG logo

### Backend (FastAPI)
- **Authentication**: JWT tokens + Google OAuth
- **Database**: PostgreSQL (Supabase) for book metadata
- **Vector Store**: ChromaDB for embeddings
- **LLM Integration**: Google Gemini for intelligent responses
- **Semantic Search**: SentenceTransformers (all-mpnet-base-v2)

## 📦 Project Structure

```
litscholar/
├── frontend/                    # React frontend
│   ├── public/                  # Static assets
│   │   └── litscholar-icon.svg
│   ├── src/
│   │   ├── components/          # Reusable UI components
│   │   │   ├── Navbar.jsx
│   │   │   ├── Footer.jsx
│   │   │   ├── SearchBar.jsx
│   │   │   ├── BookCard.jsx
│   │   │   └── LitScholarLogo.jsx
│   │   ├── context/             # Global state
│   │   │   └── AppContext.jsx
│   │   ├── pages/               # Page components
│   │   │   ├── Auth.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   ├── BookDetail.jsx
│   │   │   ├── Profile.jsx
│   │   │   └── NotFound.jsx
│   │   ├── services/            # API integration
│   │   │   └── api.js
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   └── package.json
│
└── backend/                      # FastAPI backend
    ├── assistant/                # AI librarian logic
    │   ├── librarian.py
    │   ├── router.py
    │   └── schemas.py
    ├── auth/                      # Authentication
    │   ├── oauth.py
    │   ├── router.py
    │   └── schemas.py
    ├── books/                      # Book routes
    │   └── router.py
    ├── core/                        # Core config
    │   ├── config.py
    │   ├── database.py
    │   ├── db.py
    │   └── security.py
    ├── data/                         # CSV datasets
    │   ├── book_raw.csv
    │   └── books_clean.csv
    ├── llm/                           # LLM clients
    │   ├── gemini_client.py
    │   └── ollama_client.py
    ├── retrieval/                     # Search & embeddings
    │   ├── chroma_client.py
    │   ├── retriever.py
    │   ├── supabase_fetch.py
    │   └── test_retriever.py
    ├── scripts/                        # Data pipeline scripts
    │   ├── build_chroma_embeddings.py
    │   ├── clean_books_csv.py
    │   ├── insert_cleaned_books.py
    │   ├── pipeline_checks.py
    │   └── run_pipeline.py
    ├── users/                          # User routes
    │   ├── router.py
    │   └── schemas.py
    ├── utils/                           # Helpers
    │   └── keyword_extractor.py
    ├── chroma_store/                    # ChromaDB storage (created at runtime)
    ├── main.py                           # FastAPI app
    ├── requirements.txt                  # Python dependencies
    └── .env                               # Environment variables
```

## 🛠️ Installation with Conda

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Backend Setup with Conda
```bash
cd backend

# Create conda environment
conda create -n litscholar python=3.10 -y

# Activate environment
conda activate litscholar

# Install dependencies
pip install -r requirements.txt
```

### Environment Configuration
Create a `.env` file in the backend directory:
```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/litscholar

# JWT Settings
JWT_SECRET=your_jwt_secret_key_change_this_in_production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# OAuth / Session
SESSION_SECRET_KEY=your_session_secret_key_change_this
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback

# Frontend
FRONTEND_URL=http://localhost:5173

# API Keys
GEMINI_API_KEY=your_gemini_api_key

# CORS
CORS_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]

# Environment
ENVIRONMENT=development
```

## 🚀 Running the Application

### Start Backend Server
```bash
cd backend
conda activate litscholar
uvicorn main:app --reload --port 8000
```

### Start Frontend Development Server
```bash
cd frontend
npm run dev
```

Visit `http://localhost:5173` to use LitScholar!

## 📊 Data Pipeline

Run the complete data pipeline to populate your database and vector store:

```bash
cd backend
conda activate litscholar
python scripts/run_pipeline.py
```

This executes:
1. **Clean CSV** - Removes duplicates and invalid entries
2. **Insert to Supabase** - Stores cleaned book data
3. **Generate Embeddings** - Creates vector embeddings in ChromaDB

### Individual Pipeline Steps
```bash
# Step 1: Clean raw CSV
python scripts/clean_books_csv.py

# Step 2: Insert cleaned data to Supabase
python scripts/insert_cleaned_books.py

# Step 3: Build Chroma embeddings
python scripts/build_chroma_embeddings.py
```

## 🔍 API Endpoints

### Authentication
- `POST /auth/login` - Email/password login
- `POST /auth/register` - Create new account
- `POST /auth/refresh` - Refresh access token
- `GET /auth/google/login` - Google OAuth login
- `GET /auth/google/callback` - Google OAuth callback

### Books
- `GET /books/search?q={query}` - Search books
- `GET /books/{book_id}` - Get book details

### Assistant (AI Librarian)
- `POST /assistant/ask` - Ask the AI librarian a question

### Users
- `GET /users/me` - Get current user info

## 🧪 Testing

### Test Semantic Search
```bash
cd backend
conda activate litscholar
python retrieval/test_retriever.py
```

### Test Image URLs
```bash
cd backend
conda activate litscholar
python scripts/image_test_and_open.py
```

## 📝 Conda Commands Cheat Sheet

```bash
# Create environment
conda create -n litscholar python=3.10 -y

# Activate environment
conda activate litscholar

# Deactivate environment
conda deactivate

# List all environments
conda env list

# Remove environment
conda env remove -n litscholar

# Export environment
conda env export > environment.yml

# Create from exported file
conda env create -f environment.yml
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request


---

Built with ❤️ by Rajnish Kumar