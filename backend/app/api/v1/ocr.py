import os
import uuid
from typing import Any, Dict

from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from arq import create_pool
from arq.connections import RedisSettings
from arq.jobs import Job

from app.core.redis import get_redis

router = APIRouter()


async def get_arq_pool():
    return await create_pool(
        RedisSettings(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
        )
    )


@router.post("/parse")
async def ocr_parse(
    file: UploadFile = File(...),
    chat_id: str | None = Query(default=None),  # чтобы сохранить черновик для телеги
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Upload an image file")

    tmp_dir = os.getenv("OCR_TMP_DIR", os.path.join(os.getcwd(), "tmp"))
    os.makedirs(tmp_dir, exist_ok=True)

    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in [".jpg", ".jpeg", ".png", ".webp", ".bmp"]:
        ext = ".jpg"

    local_id = uuid.uuid4().hex
    tmp_path = os.path.join(tmp_dir, f"receipt_{local_id}{ext}")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")

    with open(tmp_path, "wb") as f:
        f.write(data)

    redis_pool = await get_arq_pool()
    job = await redis_pool.enqueue_job("ocr_parse_job", tmp_path)

    # сохраняем черновик "в процессе" для телеги
    if chat_id:
        r = get_redis()
        ttl = int(os.getenv("OCR_DRAFT_TTL_SECONDS", "7200"))
        await r.set(f"ocr:draft:{chat_id}", job.job_id, ex=ttl)

    return {"task_id": job.job_id}


@router.get("/tasks/{task_id}")
async def ocr_task_status(task_id: str):
    redis_pool = await get_arq_pool()
    job = Job(task_id, redis_pool)

    status = await job.status()
    if status == "complete":
        result = await job.result()

        # TTL на результат (опционально: если хочешь хранить отдельно)
        # Но ARQ сам хранит, тут просто отдаём.
        return {"status": "complete", "result": result}

    return {"status": status}


@router.post("/draft/{chat_id}/save")
async def ocr_draft_save(chat_id: str, payload: Dict[str, Any]):
    """
    Сохраняем ИСПРАВЛЕННЫЙ пользователем список items,
    чтобы потом отправить на /receipts.
    """
    if "items" not in payload:
        raise HTTPException(status_code=400, detail="items is required")

    r = get_redis()
    ttl = int(os.getenv("OCR_DRAFT_TTL_SECONDS", "7200"))
    await r.set(f"ocr:draft:items:{chat_id}", str(payload), ex=ttl)
    return {"ok": True}


@router.get("/draft/{chat_id}")
async def ocr_draft_get(chat_id: str):
    r = get_redis()
    task_id = await r.get(f"ocr:draft:{chat_id}")
    items = await r.get(f"ocr:draft:items:{chat_id}")
    return {"task_id": task_id, "edited_items": items}
