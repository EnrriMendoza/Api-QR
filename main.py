from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import qrcode
from PIL import Image
from io import BytesIO
import base64
import random

app = FastAPI()
cdc_storage = {}  # {(qr_id, session_id): cdc_id}

# ---- CORS ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite GitHub Pages y APEX
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- MODELOS ----
class QRRequest(BaseModel):
    session_id: str

class CDCRequest(BaseModel):
    qr_id: int
    cdc_id: str
    session_id: str

# ---- HANDLER PARA PRE-REQUEST (CORS) ----
@app.options("/{rest_of_path:path}")
async def preflight_handler(request: Request, rest_of_path: str):
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
            "Access-Control-Allow-Headers": "*"
        }
    )

# ---- GENERAR QR ----
@app.post("/qr/generador")
def generar_qr(request: QRRequest):
    qr_id = random.randint(1, 999999)
    qr_data = f"https://enrrimendoza.github.io/Api-QR-generator/?qr_id={qr_id}&session_id={request.session_id}"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img = img.resize((400, 400), resample=Image.LANCZOS)

    buffer = BytesIO()
    img.save(buffer, format="PNG", optimize=True)
    qr_bytes = buffer.getvalue()

    return {"qr": base64.b64encode(qr_bytes).decode(), "url": qr_data, "qr_id": qr_id}

# ---- GUARDAR CDC ----
@app.post("/qr/guardar-cdc")
def guardar_cdc(request: CDCRequest):
    if not request.cdc_id.strip():
        raise HTTPException(status_code=400, detail="cdc_id no puede estar vacío")

    key = (request.qr_id, request.session_id.strip())
    cdc_storage[key] = request.cdc_id.strip()
    return {"status": "ok", "message": "CDC guardado", "qr_id": request.qr_id}

# ---- VERIFICAR CDC ----
@app.get("/qr/verificar-cdc")
def verificar_cdc(qr_id: int = Query(...), session_id: str = Query(...)):
    key = (qr_id, session_id.strip())
    return {"cdc_id": cdc_storage.get(key)}
