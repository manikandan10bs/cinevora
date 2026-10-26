# Cinevora Deployment Helper Script
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "       Cinevora Deployment Guide          " -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/3] Push to GitHub:" -ForegroundColor Yellow
Write-Host "1. Go to https://github.com/new and create a new repository named: cinevora"
Write-Host "2. Run this command in PowerShell to push your committed code:"
Write-Host "   git push -u origin main" -ForegroundColor Green
Write-Host ""

Write-Host "[2/3] Deploy Frontend to Vercel (Free & Instant):" -ForegroundColor Yellow
Write-Host "1. Go to https://vercel.com/new"
Write-Host "2. Import your GitHub repository: cinevora"
Write-Host "3. Set Root Directory to: frontend_ui"
Write-Host "4. Build Command: npm run build"
Write-Host "5. Output Directory: dist"
Write-Host "6. Add Environment Variable: VITE_API_BASE_URL = <Your Deployed Backend URL>"
Write-Host "7. Click Deploy!"
Write-Host ""

Write-Host "[3/3] Deploy Backend to Render (Free & Instant):" -ForegroundColor Yellow
Write-Host "1. Go to https://dashboard.render.com"
Write-Host "2. Click 'New Web Service' -> Connect your GitHub repo 'cinevora'"
Write-Host "3. Environment: Python 3"
Write-Host "4. Build Command: pip install -r requirements.txt"
Write-Host "5. Start Command: uvicorn app.main:app --host 0.0.0.0 --port `$PORT"
Write-Host "6. Add Environment Variables:"
Write-Host "   - GEMINI_API_KEY = your_gemini_api_key"
Write-Host "   - GEMINI_MODEL = gemini-3.5-flash-lite"
Write-Host "7. Click Create Web Service!"
Write-Host ""
Write-Host "Your Cinevora platform is ready to launch globally!" -ForegroundColor Green
