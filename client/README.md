# LitScholar client

React 18 + Vite frontend for LitScholar: dashboard, book detail, AI librarian chat, recommendations, pricing, and profile.

## Stack

- **Vite** — dev server and build
- **Tailwind CSS** — styling (`src/index.css` for global background, overlays, toast theming)
- **React Router** — `/`, `/auth`, `/dashboard`, `/book/:bookId`, `/pricing`, `/profile`, etc.
- **Axios** — `src/services/api.js` (auth vs RAG instances; `withCredentials` for cookies)
- **React Toastify** — notifications

## Environment

Create `client/.env` (or `.env.local`) from your deployment values:

| Variable | Purpose |
|----------|---------|
| `VITE_AUTH_API_URL` | Auth service base URL (default `http://localhost:8000`) |
| `VITE_RAG_API_URL` | RAG / books API base URL (default `http://localhost:8001`) |
| `VITE_EMAIL_API_URL` | Email service (default `http://localhost:8002`) |
| `VITE_PAYMENT_API_URL` | Payment service (default `http://localhost:8003`) |
| `VITE_ENVIRONMENT` | e.g. `development` / `production` |

## Auth behavior

- **Auth service** issues JWTs in **httpOnly** cookies (`access_token`, `refresh_token`) on login, register, refresh, and Google OAuth redirect.
- The client uses **`withCredentials: true`** so the browser sends those cookies to the auth origin.
- The **RAG** service often runs on another port/origin; cookies are not shared. The app keeps a short-lived **in-memory** access token from login/refresh **response bodies** only (not `localStorage`) to send `Authorization: Bearer …` to RAG. See `src/services/api.js` and `src/services/auth.js`.

## Splash screen

On first load per **browser tab session**, a splash overlay runs (`src/components/SplashScreen.jsx`). It stays fully visible for **at least 4 seconds**, then fades out before the app continues. Dismissal is remembered with `sessionStorage` key `litscholar_splash_seen`. Clear it in dev tools to see the splash again.

## Commands

```bash
npm install
npm run dev      # http://localhost:5173
npm run build
npm run preview
```

## Project layout (high level)

```
src/
├── App.jsx              # Routes + splash gate
├── main.jsx
├── index.css            # Global background, animations, toast overrides
├── context/AppContext.jsx
├── components/          # SplashScreen, Navbar, ProtectedRoute, …
├── pages/               # Auth, Dashboard, BookDetail, …
├── services/            # api.js, auth.js, books.js, payments, …
└── utils/               # tokens.js (legacy cleanup), cookies helpers
```

For the full architecture, see the repository root `README.md`.
