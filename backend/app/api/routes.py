import logging
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional

from app.schemas.models import SyncUrlRequest, SyncSummary, HealthResponse
from app.services.imdb_service import IMDbService
from app.services.csv_service import CSVService

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

@router.post("/sync/imdb-url", response_model=SyncSummary)
async def sync_imdb_url(payload: SyncUrlRequest):
    """
    Kullanıcının herkese açık IMDb URL'si (Ratings veya Watchlist) üzerinden
    izleme ve puanlama verilerini otomatik olarak çeker.
    """
    try:
        summary = IMDbService.sync_from_url(payload.url, payload.target)
        if summary.total_items == 0:
            raise HTTPException(
                status_code=404,
                detail="Belirtilen IMDb sayfasında film/dizi bulunamadı. Lütfen profil veya listenizin 'Public' (Herkese Açık) olduğundan emin olun."
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
