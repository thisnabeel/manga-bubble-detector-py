# Deploying to Railway

Railway will auto-detect Python and use the `Procfile` to start the server. The model (`best.pt`, 6MB) is committed directly to the repo.

---

## 1. Push to a git repo

```bash
cd bubble-detector-api
git init
git add .
git commit -m "initial"
gh repo create bubble-detector-api --public --source=. --push
```

---

## 2. Create the Railway project

1. Go to [railway.app](https://railway.app) and click **New Project**
2. Choose **Deploy from GitHub repo** and select your repo
3. Railway builds and deploys automatically — no environment variables needed

Railway sets `PORT` automatically and the `Procfile` reads it.

---

## 3. Check it works

Railway gives you a public URL like `https://bubble-detector-api-production.up.railway.app`.

```bash
curl https://your-service.up.railway.app/health
# {"status":"ok","model_loaded":true}

curl -X POST https://your-service.up.railway.app/predict/url \
  -H "Content-Type: application/json" \
  -d '{"image_url": "https://your-s3-url.jpg"}'
```

---

## Notes

- Railway's free tier sleeps after inactivity — first request after sleep will be slow (~5–10s cold start + model load). Upgrade to the Hobby plan ($5/mo) to avoid sleeping.
- Inference runs on CPU. Expect ~1–3 seconds per image at `imgsz=1024`.
- When you retrain the model, just copy the new `best.pt` over and push to git — Railway redeploys automatically.
