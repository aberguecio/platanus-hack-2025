# Environment Variables Setup

## Frontend Environment Variables

Create a `.env.local` file in the `frontend/` directory:

```bash
# API Backend URL
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**For Production:**
```bash
NEXT_PUBLIC_API_URL=https://your-backend-domain.com
```

## Backend Environment Variables

The backend already uses environment variables from the `.env` file in the project root.

Add the following to your `.env` file:

```bash
# Frontend URL for magic links
FRONTEND_URL=http://localhost:3000

# Database URL (already configured)
DATABASE_URL=sqlite:///./app.db

# Other existing variables...
# ANTHROPIC_API_KEY=...
# TELEGRAM_BOT_TOKEN=...
```

**For Production:**
```bash
FRONTEND_URL=https://your-frontend-domain.com
DATABASE_URL=postgresql://user:pass@host:port/db
```

## Summary

- **Frontend**: Uses `NEXT_PUBLIC_API_URL` (defaults to `http://localhost:8000`)
- **Backend**: Uses `FRONTEND_URL` (defaults to `http://localhost:3000`)
- Both have fallback defaults for local development
- All hardcoded URLs have been replaced with environment variables
