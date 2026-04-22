# TikTok Automation Bot - Deployment Guide

This guide covers deploying the complete TikTok automation solution:
1. **Local Bot** - Runs on your computer with AdsPower
2. **Cloud Dashboard** - Hosted on Vercel (frontend) + Render (backend)
3. **Database** - Supabase (primary) + MongoDB (auth/billing)

---

## 1. Supabase Setup (Database)

### Create Project
1. Go to [supabase.com](https://supabase.com) and create a new project
2. Note your **Project URL** and **Anon Key** (Settings > API)

### Create Tables
1. Go to SQL Editor in your Supabase dashboard
2. Copy and paste the contents of `/app/supabase_schema.sql`
3. Click "Run" to create all tables

### Enable Realtime
1. Go to Database > Replication
2. Enable realtime for: `comment_reports`, `dm_reports`, `post_reports`, `live_logs`

### Update Local Bot
Edit `/app/downloads/tiktok_commenter.py` and update these lines (around line 32-33):
```python
SUPABASE_URL = "your-project-url"
SUPABASE_KEY = "your-anon-key"
```

### Update Frontend
Edit `/app/frontend/src/lib/supabase.js` and update:
```javascript
const supabaseUrl = 'your-project-url';
const supabaseKey = 'your-anon-key';
```

---

## 2. Backend Deployment (Render)

### Prerequisites
- [Render](https://render.com) account
- MongoDB Atlas database (or use Render's managed MongoDB)

### Deploy Steps

1. **Create Web Service** on Render
   - Connect your GitHub repo
   - Root Directory: `backend`
   - Runtime: Python
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn server:app --host 0.0.0.0 --port 8001`

2. **Environment Variables** (add in Render dashboard):
```
MONGO_URL=mongodb+srv://username:password@cluster.mongodb.net
DB_NAME=tiktok_bot
JWT_SECRET=your-secure-secret-key-change-this
STRIPE_API_KEY=sk_test_... (get from Stripe Dashboard)
STRIPE_WEBHOOK_SECRET=whsec_... (get from Stripe webhooks)
RESEND_API_KEY=re_... (get from Resend Dashboard)
SENDER_EMAIL=your-verified@email.com
CORS_ORIGINS=https://your-frontend.vercel.app
```

3. **Deploy** - Render will auto-deploy on push to main branch

### Get Backend URL
After deployment, note your Render URL: `https://your-app.onrender.com`

---

## 3. Frontend Deployment (Vercel)

### Prerequisites
- [Vercel](https://vercel.com) account
- Your deployed backend URL

### Deploy Steps

1. **Import Project** on Vercel
   - Connect your GitHub repo
   - Framework Preset: Create React App
   - Root Directory: `frontend`

2. **Environment Variables** (add in Vercel dashboard):
```
REACT_APP_BACKEND_URL=https://your-backend.onrender.com
REACT_APP_SUPABASE_URL=your-supabase-project-url
REACT_APP_SUPABASE_ANON_KEY=your-supabase-anon-key
```

3. **Build Settings**:
   - Build Command: `npm run build` (or `yarn build`)
   - Output Directory: `build`
   - Install Command: `yarn install`

4. **Deploy** - Vercel will auto-deploy on push

### Custom Domain (Optional)
1. Go to Settings > Domains
2. Add your custom domain
3. Update CORS_ORIGINS in your backend

---

## 4. Stripe Webhook Setup

After deploying backend:

1. Go to [Stripe Dashboard](https://dashboard.stripe.com/webhooks)
2. Add endpoint: `https://your-backend.onrender.com/api/webhook/stripe`
3. Select events: `checkout.session.completed`, `customer.subscription.*`
4. Copy the webhook secret and add to backend env as `STRIPE_WEBHOOK_SECRET`

---

## 5. Local Bot Setup

### Requirements
- Python 3.9+
- AdsPower browser
- pip packages: `requests flask playwright supabase`

### Setup Steps

1. **Install Dependencies**:
```bash
pip install requests flask playwright supabase
playwright install chromium
```

2. **Download the Bot**:
   - Download from dashboard: `/api/download-tiktok-commenter`
   - Or copy `/app/downloads/tiktok_commenter.py`

3. **Configure**:
   Edit the file and update:
   - Line 32-33: Your Supabase URL and Key
   - Line 55: Your cloud API URL (optional, for backup sync)

4. **Run**:
```bash
python tiktok_commenter.py
```

5. **Open Dashboard**: http://localhost:9000

---

## Environment Variables Summary

### Backend (.env or Render)
| Variable | Description | Required |
|----------|-------------|----------|
| MONGO_URL | MongoDB connection string | Yes |
| DB_NAME | Database name | Yes |
| JWT_SECRET | Secret for JWT tokens | Yes |
| STRIPE_API_KEY | Stripe secret key | For billing |
| STRIPE_WEBHOOK_SECRET | Stripe webhook secret | For billing |
| RESEND_API_KEY | Resend email API key | For emails |
| SENDER_EMAIL | Verified sender email | For emails |
| CORS_ORIGINS | Allowed frontend origins | Yes |

### Frontend (.env or Vercel)
| Variable | Description | Required |
|----------|-------------|----------|
| REACT_APP_BACKEND_URL | Backend API URL | Yes |
| REACT_APP_SUPABASE_URL | Supabase project URL | Yes |
| REACT_APP_SUPABASE_ANON_KEY | Supabase anon key | Yes |

### Local Bot (in code)
| Variable | Description |
|----------|-------------|
| SUPABASE_URL | Supabase project URL |
| SUPABASE_KEY | Supabase anon key |

---

## Architecture

```
                    +-----------------+
                    |  Supabase       |
                    |  (PostgreSQL)   |
                    |  - comments     |
                    |  - DMs          |
                    |  - posts        |
                    +-----------------+
                           ^
                           |
    +----------------------|----------------------+
    |                      |                      |
+--------+            +--------+            +--------+
| Local  |            | React  |            | FastAPI|
| Bot    | ---------> | Frontend| <-------> | Backend|
| (9000) |    sync    | (Vercel)|    API    |(Render)|
+--------+            +--------+            +--------+
    |                                            |
    v                                            v
+--------+                              +--------+
|AdsPower|                              |MongoDB |
|Browser |                              |(Auth)  |
+--------+                              +--------+
```

---

## Troubleshooting

### Backend won't start
- Check logs in Render dashboard
- Verify MONGO_URL is correct and IP is whitelisted
- Ensure all required packages are in requirements.txt

### Frontend won't build
- Run `yarn install` locally to check for errors
- Ensure all imports are correct
- Check Vercel build logs

### Supabase connection issues
- Verify URL and Key are correct
- Check if RLS policies allow access
- Ensure tables exist (run schema SQL)

### Local bot can't sync
- Check if Supabase credentials are correct in the code
- Ensure supabase package is installed: `pip install supabase`
- Check network connectivity

---

## Support

For issues, check:
1. Render/Vercel deployment logs
2. Supabase logs (Database > Logs)
3. Browser console for frontend errors
4. Terminal output for local bot errors
