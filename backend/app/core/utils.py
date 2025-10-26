import hashlib
from passlib.context import CryptContext
from fastapi import Request

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    # 使用 SHA-256 預處理密碼，避免 bcrypt 的 72 字節限制
    password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
    return pwd_context.hash(password_hash)

def get_real_ip(request: Request) -> str:
    """
    獲取真實的客戶端 IP 地址
    優先順序：X-Forwarded-For > X-Real-IP > request.client.host
    """
    # 檢查 X-Forwarded-For 標頭（可能包含多個 IP，取第一個）
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For 可能包含多個 IP，用逗號分隔，取第一個
        return forwarded_for.split(",")[0].strip()
    
    # 檢查 X-Real-IP 標頭
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    
    # 最後回退到 request.client.host
    return request.client.host if request.client.host else "unknown"