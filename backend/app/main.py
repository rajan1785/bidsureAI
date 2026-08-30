from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import init_db

app = FastAPI(title="BidSure AI Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()


@app.get("/health")
def health():
    return {"status": "ok"}


def register_routers():
    from app.routers import audit, bidders, bids, dashboard, tenders

    for r in (tenders.router, bidders.router, bids.router, dashboard.router, audit.router):
        app.include_router(r, prefix="/api/v1")


try:
    register_routers()
except ImportError:
    # Routers land in Task 6; skeleton stays runnable until then.
    pass
