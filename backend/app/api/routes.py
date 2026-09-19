import os
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from app.schemas.models import SyncUrlRequest, SyncSummary, HealthResponse

from app.schemas.graph_models import NetworkGraphResponse
from app.services.imdb_service import IMDbService
from app.services.csv_service import CSVService
from app.services.letterboxd_service import LetterboxdService
from app.services.graph_service import GraphService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Sync & Import"])

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Sistem ve API sağlık kontrolü."""
    return HealthResponse(
        status="healthy",
        service="SuggestIT Core API",
        version="0.1.0"
    )

@router.post("/graph/generate", response_model=NetworkGraphResponse, tags=["Taste Graph"])
async def generate_taste_graph(titles: list[dict]):
    """
    Film ve dizi listesinden kullanıcının Taste Network Graph'ını ve Sinematik Arketipini üretir.
    """
    try:
        from app.schemas.models import TitleItem
        parsed_titles = [TitleItem(**t) if isinstance(t, dict) else t for t in titles]
        graph_data = GraphService.generate_graph(parsed_titles)
        return graph_data
    except Exception as e:
        logger.error(f"Graph üretim hatası: {e}")
        raise HTTPException(status_code=500, detail=f"Ağ grafiği üretilemedi: {str(e)}")

@router.get("/graph/preview", response_class=HTMLResponse, tags=["Taste Graph"])
async def preview_taste_graph():
    """
    Kullanıcının Zevk Ağ Grafiğini (Taste Network Graph) tarayıcıda doğrudan
    interaktif ve animasyonlu olarak görselleştiren D3.js paneli.
    """
    template_path = os.path.join(os.path.dirname(__file__), "..", "templates", "graph_preview.html")
    if not os.path.exists(template_path):
        raise HTTPException(status_code=404, detail="Preview şablonu bulunamadı.")
    with open(template_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

@router.post("/sync/letterboxd-url", response_model=SyncSummary)
async def sync_letterboxd_url(payload: SyncUrlRequest):

    """
    Kullanıcının Letterboxd profil URL'si veya kullanıcı adı üzerinden
    son izleme ve puanlama verilerini anında çeker.
    """
    try:
        summary = LetterboxdService.sync_from_username_or_url(payload.url)
        return summary
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Letterboxd sync hatası: {e}")
        raise HTTPException(status_code=500, detail=f"Letterboxd verisi çekilemedi: {str(e)}")

@router.post("/sync/imdb-url", response_model=SyncSummary)
async def sync_imdb_url(payload: SyncUrlRequest):
    """
    Kullanıcının herkese açık IMDb URL'si (Ratings veya Watchlist) üzerinden
    izleme ve puanlama verilerini çeker.
    """
    try:
        summary = IMDbService.sync_from_url(payload.url, payload.target)
        if summary.total_items == 0:
            raise HTTPException(
                status_code=403,
                detail=(
                    "IMDb AWS WAF bot koruması nedeniyle doğrudan URL erişimini kısıtladı. "
                    "Lütfen IMDb masaüstü profilinizden 'Export' butonuna basarak indirdiğiniz CSV dosyasını "
                    "'/api/v1/import/csv' ucuna yükleyin veya Letterboxd profil linkinizi kullanın."
                )
            )
        return summary
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"IMDb sync sırasında beklenmeyen hata: {e}")
        raise HTTPException(status_code=500, detail=f"Veri çekilirken sunucu hatası oluştu: {str(e)}")


@router.post("/import/csv", response_model=SyncSummary)
async def import_csv_file(
    file: UploadFile = File(...),
    platform: Optional[str] = Form("auto")
):
    """
    IMDb veya Letterboxd'den dışa aktarılan CSV dosyasını sisteme yükler ve normalize eder.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Yalnızca .csv uzantılı dosyalar desteklenmektedir.")

    try:
        content_bytes = await file.read()
        file_text = content_bytes.decode("utf-8", errors="replace")
        
        summary = CSVService.process_uploaded_csv(file_text, platform=platform)
        if summary.total_items == 0:
            raise HTTPException(status_code=400, detail="Yüklenen CSV dosyasında geçerli bir veri satırı bulunamadı.")
            
        return summary
    except Exception as e:
        logger.error(f"CSV import hatası: {e}")
        raise HTTPException(status_code=500, detail=f"CSV işlenirken hata oluştu: {str(e)}")
