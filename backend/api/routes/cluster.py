"""Clustering routes — POST /cluster."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from rq import Queue

from api.deps import get_rq_queue
from models.wallet import Address

router = APIRouter(prefix="/cluster", tags=["cluster"])


@router.post("", status_code=202)
async def start_cluster(
    request: Address,
    queue: Queue = Depends(get_rq_queue),
):
    """Enqueue a clustering job around a seed wallet."""
    job = queue.enqueue(
        "workers.cluster_job.run_cluster",
        kwargs={"address": request.address, "chain": request.chain.value},
        job_timeout=300,
    )
    return {"job_id": job.id, "status": "queued"}
