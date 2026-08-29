from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import init_db

app = FastAPI(title="ComplyGeM Backend", version="1.0.0")

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

    app.include_router(tenders.router)
    app.include_router(bidders.router)
    app.include_router(bids.router)
    app.include_router(dashboard.router)
    app.include_router(audit.router)


try:
    register_routers()
except ImportError:
    # Routers land in Task 6; skeleton stays runnable until then.
    pass
