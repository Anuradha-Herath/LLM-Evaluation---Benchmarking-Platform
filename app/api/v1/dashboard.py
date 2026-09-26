from pathlib import Path
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/dashboard", tags=["Dashboard UI"])


@router.get(
    "",
    response_class=HTMLResponse,
    status_code=status.HTTP_200_OK,
    summary="Access Evaluation Dashboard",
    description="Serves the single-page engineering dashboard web UI.",
)
async def get_dashboard_ui() -> HTMLResponse:
    dashboard_html_path = Path(__file__).resolve().parent.parent.parent / "static" / "dashboard.html"
    if not dashboard_html_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard static UI file not found.",
        )

    with open(dashboard_html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    return HTMLResponse(content=html_content, status_code=status.HTTP_200_OK)
