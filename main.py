from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import qrcode
from PIL import Image
from io import BytesIO
import base64
import random

# --------------------------------------------------------
# Configuración principal
# --------------------------------------------------------
app = FastAPI()
cdc_storage = {}  # {(qr_id, session_id): cdc_id}

# Permitir solicitudes desde cualquier origen (GitHub Pages, APEX, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------------
# Modelos de datos
# --------------------------------------------------------
class QRRequest(BaseModel):
    session_id: str

class CDCRequest(BaseModel):
    qr_id: int
    cdc_id: str
    session_id: str

# --------------------------------------------------------
# Respuesta a preflight (CORS OPTIONS)
# --------------------------------------------------------
@app.options("/{rest_of_path:path}")
async def preflight_handler(request: Request, rest_of_path: str):
    """Responde correctamente a las peticiones OPTIONS para evitar errores CORS."""
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
            "Access-Control-Allow-Headers": "*"
        }
    )

# --------------------------------------------------------
# Generar QR
# --------------------------------------------------------
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

    return {
        "qr": base64.b64encode(qr_bytes).decode(),
        "url": qr_data,
        "qr_id": qr_id
    }

# --------------------------------------------------------
# Guardar CDC (desde la web del celular)
# --------------------------------------------------------
@app.post("/qr/guardar-cdc")
def guardar_cdc(request: CDCRequest):
    if not request.cdc_id or not request.cdc_id.strip():
        raise HTTPException(status_code=400, detail="cdc_id no puede estar vacío")

    if not request.session_id or not str(request.session_id).strip():
        raise HTTPException(status_code=400, detail="session_id no puede estar vacío")

    normalized_session_id = str(request.session_id).strip()
    key = (request.qr_id, normalized_session_id)
    cdc_storage[key] = request.cdc_id.strip()

    return {
        "status": "ok",
        "message": f"CDC '{request.cdc_id}' guardado correctamente",
        "qr_id": request.qr_id,
        "session_id": normalized_session_id
    }

# --------------------------------------------------------
# Verificar si APEX ya tiene un CDC asociado
# --------------------------------------------------------
@app.get("/qr/verificar-cdc")
def verificar_cdc(qr_id: int = Query(...), session_id: str = Query(...)):
    key = (qr_id, session_id.strip())
    cdc_id = cdc_storage.get(key)
    return {"cdc_id": cdc_id, "found": cdc_id is not None, "qr_id": qr_id}
