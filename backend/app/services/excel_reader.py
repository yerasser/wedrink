from __future__ import annotations

import io
import pandas as pd
from fastapi import HTTPException, UploadFile


def read_xlsx_df(file: UploadFile) -> pd.DataFrame:
    if not file.filename or not file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Upload an Excel file (.xlsx/.xls)")

    content = file.file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        df = pd.read_excel(io.BytesIO(content), header=0)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Cannot read Excel: {e}")

    df.columns = [str(c).strip().lower() for c in df.columns]
    df = df.dropna(how="all")
    return df
