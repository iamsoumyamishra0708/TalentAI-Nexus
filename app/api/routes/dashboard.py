from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["Frontend HR & Candidate Portal"])

# Exact path: app/api/routes/dashboard.py -> parent(routes) -> parent(api) -> parent(app) / templates / dashboard.html
TEMPLATE_PATH = Path(__file__).resolve().parent.parent.parent / "templates" / "dashboard.html"

@router.get("/dashboard", response_class=HTMLResponse)
async def serve_hr_dashboard():
    """Reads and serves the standalone HTML Command Center."""
    if not TEMPLATE_PATH.exists():
        return HTMLResponse(
            content=f"<h3>Template file missing at: {TEMPLATE_PATH}</h3>",
            status_code=500
        )
    return HTMLResponse(content=TEMPLATE_PATH.read_text(encoding="utf-8"))