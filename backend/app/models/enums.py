import enum


class UserRole(str, enum.Enum):
    admin = "admin"
    operator = "operator"


class ReceiptStatus(str, enum.Enum):
    uploaded = "uploaded"
    processing = "processing"
    parsed = "parsed"
    edited = "edited"
    applied = "applied"
    failed = "failed"
