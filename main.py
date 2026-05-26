import io
import json
import os

import pdfplumber
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

load_dotenv()

from database import engine, Base, get_db
from models import Contrato

app = FastAPI(title="megumin-estate-ai")

Base.metadata.create_all(bind=engine)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openai/gpt-4o-mini"

MEGUMIN_SYSTEM_PROMPT = """Eres Megumin, una asistente inmobiliaria amable y servicial.
Tu ÚNICA fuente de información son los contratos que se te proporcionan en el contexto.
Responde siempre en español, de forma clara y amigable.
Si la información solicitada no está en los contratos, indícalo amablemente sin inventar datos."""


class ChatRequest(BaseModel):
    mensaje: str


SYSTEM_PROMPT = """You are a real estate contract data extractor.
Your ONLY output must be a single valid JSON object — no explanation, no markdown, no extra text.
The JSON must contain exactly these eight keys:
- "precio_alquiler": monthly rent amount as a float (null if not found)
- "penalizacion_retraso": late payment penalty as a float (null if not found)
- "fecha_inicio": lease start date as a string in ISO 8601 format YYYY-MM-DD (null if not found)
- "fecha_fin": lease end date as a string in ISO 8601 format YYYY-MM-DD (null if not found)
- "propietario": full name of the landlord/owner as a string (null if not found)
- "arrendatario": full name of the tenant as a string (null if not found)
- "direccion_inmueble": full address of the property as a string (null if not found)
- "moneda": currency code or symbol used for rent amounts as a string, e.g. "USD", "EUR", "MXN" (null if not found)

Example of valid output:
{"precio_alquiler": 1200.0, "penalizacion_retraso": 50.0, "fecha_inicio": "2025-01-01", "fecha_fin": "2026-01-01", "propietario": "Juan García", "arrendatario": "María López", "direccion_inmueble": "Calle Mayor 10, 28001 Madrid", "moneda": "EUR"}"""


def extract_text_from_pdf(file_bytes: bytes) -> str:
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)


def query_openrouter(contract_text: str) -> dict:
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "MeguminEstateAI",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Extract data from this contract:\n\n{contract_text}"},
        ],
        "temperature": 0,
    }

    response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=30)
    response.raise_for_status()

    raw_content = response.json()["choices"][0]["message"]["content"].strip()
    return json.loads(raw_content)


@app.post("/upload-contract/")
async def upload_contract(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    contract_text = extract_text_from_pdf(file_bytes)
    if not contract_text.strip():
        raise HTTPException(status_code=422, detail="Could not extract text from PDF.")

    extracted_data = query_openrouter(contract_text)

    contrato = Contrato(
        precio_alquiler=extracted_data.get("precio_alquiler"),
        penalizacion_retraso=extracted_data.get("penalizacion_retraso"),
        fecha_inicio=extracted_data.get("fecha_inicio"),
        fecha_fin=extracted_data.get("fecha_fin"),
        propietario=extracted_data.get("propietario"),
        arrendatario=extracted_data.get("arrendatario"),
        direccion_inmueble=extracted_data.get("direccion_inmueble"),
        moneda=extracted_data.get("moneda"),
    )
    db.add(contrato)
    db.commit()
    db.refresh(contrato)

    return JSONResponse(content={**extracted_data, "id": contrato.id})


@app.post("/chat/")
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    contratos = db.query(Contrato).all()

    if not contratos:
        return {
            "respuesta": (
                "¡Hola! Soy Megumin, tu asistente inmobiliaria. "
                "Aún no hay contratos registrados en el sistema. "
                "Por favor, sube uno primero usando /upload-contract/."
            )
        }

    contexto = "CONTRATOS REGISTRADOS EN EL SISTEMA:\n\n"
    for i, c in enumerate(contratos, start=1):
        contexto += (
            f"Contrato #{i} (ID: {c.id}):\n"
            f"  - Precio de alquiler mensual: {c.precio_alquiler if c.precio_alquiler is not None else 'No especificado'}\n"
            f"  - Penalización por retraso: {c.penalizacion_retraso if c.penalizacion_retraso is not None else 'No especificada'}\n"
            f"  - Fecha de inicio: {c.fecha_inicio if c.fecha_inicio else 'No especificada'}\n"
            f"  - Fecha de fin: {c.fecha_fin if c.fecha_fin else 'No especificada'}\n\n"
        )

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": MEGUMIN_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"{contexto}\nPregunta del usuario: {request.mensaje}",
            },
        ],
        "temperature": 0.7,
    }

    try:
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Error al contactar OpenRouter: {str(e)}")

    respuesta = response.json()["choices"][0]["message"]["content"].strip()
    return {"respuesta": respuesta}
