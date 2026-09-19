import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router

# Log yapılandırması
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

app = FastAPI(
    title="SuggestIT Core API",
    description="IMDb ve Letterboxd verilerini analiz eden akıllı film/dizi öneri motoru API'si.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS İzinleri (Next.js Frontend bağlantısı için)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"  # Geliştirme ortamında tüm kaynaklara izin ver
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Yönlendiricilerini Bağla
app.include_router(api_router)

@app.get("/")
def root():
    return {
        "project": "SuggestIT API",
        "version": "0.1.0",
        "docs": "/docs",
        "status": "online"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
