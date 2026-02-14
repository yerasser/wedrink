from datetime import datetime
from celery.utils.log import get_task_logger
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.enums import ReceiptStatus
from app.models.receipt import Receipt
from app.models.receipt_item import ReceiptItem
from app.services.storage import get_object, delete_object
from app.worker import celery_app
from app.services.ocr_impl import run_ocr_and_parse

logger = get_task_logger(__name__)


def _now():
    return datetime.utcnow()


@celery_app.task(bind=True, name="app.tasks.ocr_tasks.ocr_process_receipt", autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 5})
def ocr_process_receipt(self, receipt_id: int, object_key: str):
    db: Session = SessionLocal()
    try:
        # lock receipt (чтобы 2 воркера не работали одновременно)
        with db.begin():
            r = db.execute(
                select(Receipt).where(Receipt.id == receipt_id).with_for_update()
            ).scalar_one_or_none()

            if not r:
                logger.warning("receipt not found: %s", receipt_id)
                return

            # если уже applied — ничего не делаем
            if r.status == ReceiptStatus.applied:
                return

            r.status = ReceiptStatus.processing
            r.ocr_started_at = _now()
            r.ocr_error = None
            db.add(r)

        # скачать фото
        image_bytes = get_object(object_key)
        logger.info("downloaded bytes=%s", len(image_bytes))

        # OCR (пока заглушка, но структура продовая)
        raw_text, parsed_items = run_ocr_and_parse(image_bytes)


        with db.begin():
            r = db.execute(select(Receipt).where(Receipt.id == receipt_id).with_for_update()).scalar_one()

            # перезапись результатов OCR: удаляем старые items (источник истины)
            db.query(ReceiptItem).filter(ReceiptItem.receipt_id == receipt_id).delete()

            r.raw_text = raw_text
            r.status = ReceiptStatus.parsed
            r.ocr_finished_at = _now()
            db.add(r)

            db.add_all([
                ReceiptItem(
                    receipt_id=receipt_id,
                    product_code_raw=it["product_code_raw"],
                    qty=it["qty"],
                    unit_price=it.get("unit_price"),
                    line_total=it.get("line_total"),
                    product_id=None,
                    is_deleted=False,
                )
                for it in parsed_items
            ])

        # можно удалить файл сразу
        delete_object(object_key)

    except Exception as e:
        # записать failed
        try:
            with db.begin():
                r = db.execute(select(Receipt).where(Receipt.id == receipt_id).with_for_update()).scalar_one_or_none()
                if r:
                    r.status = ReceiptStatus.failed
                    r.ocr_error = str(e)
                    r.ocr_finished_at = _now()
                    db.add(r)
        finally:
            db.close()
        raise
    finally:
        db.close()

