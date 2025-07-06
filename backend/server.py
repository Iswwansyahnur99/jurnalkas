from fastapi import FastAPI, APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware

# 1. Buat aplikasi FastAPI terlebih dahulu
app = FastAPI()

# 2. Baru tambahkan middleware ke aplikasi yang sudah ada
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # Ganti dengan URL Vercel Anda jika perlu, "*" juga bisa untuk pengembangan
        "*" 
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
# Pastikan MONGO_URL dan DB_NAME sudah diatur di Environment Variables Vercel
mongo_url = os.environ.get('MONGO_URL')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME')]

# Buat router tanpa prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()

# Define Models
class Transaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tanggal: datetime = Field(default_factory=datetime.utcnow)
    keterangan: str
    jenis: str  # "pemasukan" or "pengeluaran"
    jumlah: float
    created_at: datetime = Field(default_factory=datetime.utcnow)

class TransactionCreate(BaseModel):
    tanggal: datetime
    keterangan: str
    jenis: str
    jumlah: float

class TransactionResponse(BaseModel):
    id: str
    tanggal: str
    keterangan: str
    jenis: str
    jumlah: float
    pemasukan: Optional[float] = None
    pengeluaran: Optional[float] = None

class AdminLogin(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    message: str
    token: str

class Summary(BaseModel):
    total_pemasukan: float
    total_pengeluaran: float
    saldo: float

# Admin authentication
async def verify_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != "admin_session_token":
        raise HTTPException(status_code=401, detail="Invalid authentication")
    return credentials.credentials

# Routes
@api_router.post("/login", response_model=LoginResponse)
async def login(login_data: AdminLogin):
    if login_data.username == "admin" and login_data.password == "admin":
        return LoginResponse(message="Login berhasil", token="admin_session_token")
    else:
        raise HTTPException(status_code=401, detail="Username atau password salah")

@api_router.get("/transactions", response_model=List[TransactionResponse])
async def get_transactions():
    transactions = await db.transactions.find().sort("tanggal", -1).to_list(1000)
    result = []
    
    for transaction in transactions:
        trans_response = TransactionResponse(
            id=transaction["id"],
            tanggal=transaction["tanggal"].strftime("%d %B %Y"),
            keterangan=transaction["keterangan"],
            jenis=transaction["jenis"],
            jumlah=transaction["jumlah"],
            pemasukan=transaction["jumlah"] if transaction["jenis"] == "pemasukan" else None,
            pengeluaran=transaction["jumlah"] if transaction["jenis"] == "pengeluaran" else None
        )
        result.append(trans_response)
    
    return result

@api_router.get("/summary", response_model=Summary)
async def get_summary():
    transactions = await db.transactions.find().to_list(1000)
    
    total_pemasukan = sum(t["jumlah"] for t in transactions if t["jenis"] == "pemasukan")
    total_pengeluaran = sum(t["jumlah"] for t in transactions if t["jenis"] == "pengeluaran")
    saldo = total_pemasukan - total_pengeluaran
    
    return Summary(
        total_pemasukan=total_pemasukan,
        total_pengeluaran=total_pengeluaran,
        saldo=saldo
    )

@api_router.post("/transactions", response_model=Transaction)
async def create_transaction(transaction: TransactionCreate, token: str = Depends(verify_admin)):
    transaction_dict = transaction.dict()
    transaction_obj = Transaction(**transaction_dict)
    await db.transactions.insert_one(transaction_obj.dict())
    return transaction_obj

@api_router.delete("/transactions/{transaction_id}")
async def delete_transaction(transaction_id: str, token: str = Depends(verify_admin)):
    result = await db.transactions.delete_one({"id": transaction_id})
    if result.deleted_count == 1:
        return {"message": "Transaksi berhasil dihapus"}
    else:
        raise HTTPException(status_code=404, detail="Transaksi tidak ditemukan")

@api_router.get("/")
async def root():
    return {"message": "TVRI Berkeringat Badminton API"}

# Include the router in the main app
app.include_router(api_router)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
