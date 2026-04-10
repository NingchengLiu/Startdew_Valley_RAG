"""
DEPLOYMENT_GUIDE.md - Deployment instructions for the Stardew Valley RAG Agent

This guide covers easiest deployment options with password protection.
"""

# ============================================================================
# RECOMMENDED: Railway (Easiest for beginners)
# ============================================================================

## Railway - Step by Step

### 1. Sign Up & Project Creation
- Go to https://railway.app
- Sign in with GitHub (grants access to repos automatically)
- Click "New Project" → "Deploy from GitHub repo"
- Select your repository

### 2. Configure Environment Variables
In Railway dashboard:
- Add variables:
  ```
  LLM_API_KEY=<your-api-key>
  LLM_BASE_URL=https://rsm-8430-finalproject.bjlkeng.io/v1
  LLM_MODEL=qwen3-30b-a3b-fp8
  EMBEDDINGS_API_KEY=<your-embeddings-key>
  EMBEDDINGS_BASE_URL=https://rsm-8430-a2.bjlkeng.io/v1
  EMBEDDINGS_MODEL=BAAI/bge-base-en-v1.5
  ADMIN_PASSWORD=<set-a-strong-password>
  ```

### 3. Add Start Command
In Railway settings → Deployment:
- Start Command: `cd src2 && python -m uvicorn app:app --host 0.0.0.0 --port $PORT`
- Note: Railway provides $PORT automatically

### 4. Add Password Protection to App
Update `src2/app.py` to check password:
```python
from fastapi import HTTPException, Header, status

async def verify_password(x_admin_password: str = Header(None)):
    """Verify admin password from header."""
    admin_pwd = os.getenv("ADMIN_PASSWORD")
    if not admin_pwd or x_admin_password != admin_pwd:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password"
        )
    return True

@app.get("/")
async def root(verified: bool = Depends(verify_password)):
    """Serve frontend with password protection."""
    return FileResponse("index.html")
```

### 5. Deploy
- Railway auto-deploys on git push to main
- Your app will be live at: `https://<your-project>.up.railway.app`
- Users must include header: `-H "x-admin-password: your_password"`

---

## Alternative 1: Render (Also Easy, Free Tier)

### Deploy Steps:
1. Go to https://render.com
2. Click "New +" → "Web Service"
3. Connect GitHub repo
4. Fill in:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `cd src2 && uvicorn app:app --host 0.0.0.0 --port 10000`
5. Add environment variables (same as Railway)
6. Choose "Free" tier (sleeps after 15 min of inactivity)

### Cost: FREE (with limitations)

---

## Alternative 2: Fly.io (Fast Deployment)

### Deploy Steps:
1. Install Fly CLI: `brew install flyctl`
2. Login: `flyctl auth login`
3. Initialize: `flyctl launch` (in repo root)
4. Edit `fly.toml`:
   ```toml
   [build]
   dockerfile = "Dockerfile"  # Create one (see below)
   
   [env]
   LLM_API_KEY = "your-key"
   ADMIN_PASSWORD = "strong-password"
   # ... other vars
   ```
5. Create simple `Dockerfile`:
   ```dockerfile
   FROM python:3.13-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   COPY . .
   CMD ["python", "-m", "uvicorn", "src2.app:app", "--host", "0.0.0.0", "--port", "8080"]
   ```
6. Deploy: `flyctl deploy`

### Cost: ~$5/month (generous free tier credit)

---

## Alternative 3: AWS (Most Control, Requires Setup)

### Using AWS Elastic Beanstalk:
1. Install EB CLI: `brew install awsebcli`
2. Create `Procfile` in root:
   ```
   web: cd src2 && uvicorn app:app --host 0.0.0.0 --port 8000
   ```
3. Initialize: `eb init -p python-3.11 stardew-agent`
4. Create environment: `eb create production`
5. Set environment variables: `eb setenv LLM_API_KEY=... ADMIN_PASSWORD=...`
6. Deploy: `eb deploy`

### Cost: $10-50/month depending on traffic

---

# ============================================================================
# PASSWORD PROTECTION IMPLEMENTATION
# ============================================================================

Quick implementation for any deployment:

```python
# In src2/app.py
import os
from fastapi import HTTPException, Header, status, Depends

async def verify_admin_password(x_admin_password: str = Header(None)):
    """Middleware to verify admin password."""
    required_password = os.getenv("ADMIN_PASSWORD")
    
    if not required_password:
        # No password set, allow all (development mode)
        return True
    
    if x_admin_password != required_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    return True

# Apply to protected endpoints
@app.get("/")
async def root(_: bool = Depends(verify_admin_password)):
    return FileResponse("index.html")

@app.post("/chat")
async def chat_endpoint(request: ChatRequest, _: bool = Depends(verify_admin_password)):
    # ... existing code
```

Client needs to pass password:
```bash
curl -H "x-admin-password: your_password" http://localhost:8000/
```

---

# ============================================================================
# RECOMMENDATION SUMMARY
# ============================================================================

| Platform | Ease | Cost | Best For |
|----------|------|------|----------|
| **Railway** | ⭐⭐⭐⭐⭐ | FREE | Beginners, quick deployment |
| **Render** | ⭐⭐⭐⭐ | FREE | No-effort free tier |
| **Fly.io** | ⭐⭐⭐ | $5/mo | Balance of ease and power |
| **AWS** | ⭐⭐ | $10-50/mo | Enterprise, custom config |

**RECOMMENDED FOR YOU: Railway**
- Easiest setup (connect GitHub, done)
- Automatic deployments on git push
- Free tier is generous
- No container knowledge needed

---

# ============================================================================
# QUICK DEPLOYMENT CHECKLIST
# ============================================================================

- [ ] Add `ADMIN_PASSWORD` to environment variables
- [ ] Update app.py with password verification code
- [ ] Test locally: `curl -H "x-admin-password: test" http://localhost:8000`
- [ ] Commit changes to main branch
- [ ] Create account on Railway/Render/Fly
- [ ] Connect GitHub repo to platform
- [ ] Set environment variables in dashboard
- [ ] Deploy (automatic or manual)
- [ ] Test live URL with password header
- [ ] Document URL + password for presentation

---

# ============================================================================
# ACCESSING DEPLOYED APP
# ============================================================================

### With Password Header (via curl):
```bash
curl -H "x-admin-password: mypassword123" https://your-app.up.railway.app
```

### In Browser (JavaScript):
```javascript
// In index.html
const API_URL = "https://your-app.up.railway.app";
const ADMIN_PASSWORD = "mypassword123";

fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: {
        "Content-Type": "application/json",
        "x-admin-password": ADMIN_PASSWORD
    },
    body: JSON.stringify({ query: "How do I marry Abigail?" })
});
```

### Update index.html:
```javascript
// At top of index.html <script>
const ADMIN_PASSWORD = prompt("Enter admin password:");
// ... then include password in all fetch calls
```

---

## Next Steps:
1. Choose deployment platform (Railway recommended)
2. Add password protection code to app.py
3. Update index.html to prompt for password
4. Deploy and test
5. Share URL + password with professor
"""

# NOTE: This is Markdown embedded as docstring for reference
# See actual deployment steps above for implementation
