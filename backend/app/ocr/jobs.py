import os
from app.ocr.parser import parse_receipt

async def ocr_parse_job(ctx, image_path: str):
    try:
        result = parse_receipt(image_path)
        return result
    finally:
        try:
            if image_path and os.path.exists(image_path):
                os.remove(image_path)
        except Exception:
            pass
