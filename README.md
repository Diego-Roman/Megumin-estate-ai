<div align="center">

# 🏠 Megumin Estate AI — Backend

**Plataforma SaaS de inteligencia artificial aplicada al sector inmobiliario.**  
Extracción automatizada de datos contractuales, gestión de portafolio y asistente legal con IA, diseñado para la industria PropTech.

---

![Python](https://img.shields.io/badge/Python-3.12-B967FF?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-01FFFF?style=for-the-badge&logo=fastapi&logoColor=black)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon-FF71CE?style=for-the-badge&logo=postgresql&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-ORM-B967FF?style=for-the-badge&logo=python&logoColor=white)
![OpenRouter](https://img.shields.io/badge/OpenRouter-GPT--4o--mini-01FFFF?style=for-the-badge&logo=openai&logoColor=black)
![Render](https://img.shields.io/badge/Deploy-Render-FF71CE?style=for-the-badge&logo=render&logoColor=white)

</div>

---

### 🌐 Arquitectura Separada (Microservicios)
Este repositorio contiene únicamente la **API (Backend)** construida con FastAPI. 

🖥️ **[Haz clic aquí para ver el repositorio del Frontend en Next.js](https://github.com/Diego-Roman/Megumin-estate-ai-frontend)**

---

### 🎥 Demostración del Sistema
> **Nota de Seguridad:** Para proteger las cuotas y claves de la API de Inteligencia Artificial (Open Router), el entorno de producción en Vercel se mantiene privado. 
> 
> Puedes ver el flujo completo de la plataforma, desde la carga del PDF hasta la extracción de datos, en el siguiente video:
> 
> **[👉 Ver Video Demostrativo de Megumin Estate AI](#)** *(Nota para Claude: deja el link con un # por ahora)*

---

## 📌 Descripción General

**Megumin Estate AI** es el backend de una plataforma SaaS PropTech que automatiza la extracción y gestión de datos críticos de contratos inmobiliarios mediante inteligencia artificial.

El sistema recibe documentos PDF de arrendamiento, extrae de forma estructurada campos como partes contratantes, canon mensual, fechas de vigencia y penalizaciones, y los persiste en una base de datos relacional. Adicionalmente, expone un asistente conversacional con contexto de la cartera de clientes real, capaz de responder consultas y redactar nuevos documentos legales bajo demanda.

> ⚠️ Este repositorio contiene exclusivamente el **Backend**. El frontend se encuentra en un repositorio separado.

---

## 📁 Estructura del Proyecto

```
megumin-estate-ai/
│
├── main.py              # 🚀 Punto de entrada de FastAPI: rutas, lógica de negocio e integración con IA
├── models.py            # 🗂️  Modelo ORM SQLAlchemy — tabla `contratos`
├── database.py          # 🔌 Configuración del motor SQLAlchemy y sesión de base de datos
├── reset_db.py          # 🔄 Utilidad CLI para resetear y recrear el esquema en la base de datos
│
├── requirements.txt     # 📦 Dependencias del proyecto
├── .env.example         # 🔐 Plantilla de variables de entorno requeridas
└── .gitignore
```

---

## ⚙️ Arquitectura y Flujo de Datos

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          CLIENTE (Frontend / API Consumer)              │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │ HTTP Request
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        FastAPI  (main.py)                               │
│                                                                         │
│   POST /upload-contract/   →  pdfplumber extrae texto del PDF           │
│                            →  OpenRouter (GPT-4o-mini) devuelve JSON    │
│                            →  SQLAlchemy persiste en PostgreSQL          │
│                                                                         │
│   POST /chat               →  Consulta todos los contratos en DB        │
│                            →  Construye contexto para el LLM            │
│                            →  OpenRouter (GPT-4o-mini) genera respuesta │
│                                                                         │
│   GET  /contracts          →  Lectura directa sobre PostgreSQL          │
│   PATCH /contracts/{id}/archivo  →  Actualiza pdf_url del contrato      │
│   DELETE /contracts/{id}   →  Eliminación del registro                  │
└──────────────┬──────────────────────────────┬───────────────────────────┘
               │                              │
               ▼                              ▼
  ┌────────────────────┐          ┌───────────────────────┐
  │  PostgreSQL (Neon) │          │   OpenRouter API       │
  │  Tabla: contratos  │          │   Model: gpt-4o-mini   │
  └────────────────────┘          └───────────────────────┘
```

**🔁 Flujo de extracción (núcleo del sistema):**

1. 📤 El cliente sube un archivo PDF vía `multipart/form-data`.
2. 📄 `pdfplumber` convierte el PDF en texto plano.
3. 🤖 El texto se envía a OpenRouter con un *system prompt* de extracción estructurada, que instruye al modelo a devolver un JSON con exactamente ocho campos estandarizados.
4. 💾 La respuesta JSON se deserializa y persiste en la tabla `contratos` de PostgreSQL (Neon).
5. ✅ El endpoint devuelve los datos extraídos junto con el `id` del nuevo registro.

---

## 🛣️ Endpoints

| Método   | Ruta                              | Descripción                                                                    |
|----------|-----------------------------------|--------------------------------------------------------------------------------|
| `GET`    | `/contracts`                      | 📋 Retorna todos los contratos almacenados en base de datos.                   |
| `POST`   | `/upload-contract/`               | 📤 Recibe un PDF, extrae datos con IA y guarda el contrato.                    |
| `PATCH`  | `/contracts/{contract_id}/archivo`| 🔗 Actualiza la URL del PDF almacenado (integración con UploadThing).          |
| `DELETE` | `/contracts/{contract_id}`        | 🗑️ Elimina un contrato por ID.                                                 |
| `POST`   | `/chat`                           | 💬 Consulta al asistente IA con contexto completo de la cartera de contratos.  |

### 📦 Schema de respuesta — `POST /upload-contract/`

```json
{
  "id": 1,
  "propietario": "Juan García",
  "arrendatario": "María López",
  "direccion_inmueble": "Calle Mayor 10, 28001 Madrid",
  "precio_alquiler": 1200.0,
  "penalizacion_retraso": 50.0,
  "fecha_inicio": "2025-01-01",
  "fecha_fin": "2026-01-01",
  "moneda": "EUR"
}
```

### 💬 Schema de respuesta — `POST /chat`

```json
{
  "response": "Actualmente tienes 3 contratos activos. El de mayor canon es el de la Calle Mayor..."
}
```

---

## 🗄️ Modelo de Base de Datos

**Tabla:** `contratos`

| Columna               | Tipo      | Descripción                                 |
|-----------------------|-----------|---------------------------------------------|
| `id`                  | `INTEGER` | 🔑 Clave primaria autoincremental            |
| `propietario`         | `VARCHAR` | 👤 Nombre completo del arrendador            |
| `arrendatario`        | `VARCHAR` | 👤 Nombre completo del arrendatario          |
| `direccion_inmueble`  | `VARCHAR` | 📍 Dirección completa del inmueble           |
| `precio_alquiler`     | `FLOAT`   | 💰 Canon mensual de arrendamiento            |
| `penalizacion_retraso`| `FLOAT`   | ⚠️ Penalización por pago tardío              |
| `fecha_inicio`        | `VARCHAR` | 📅 Fecha de inicio del contrato (ISO 8601)   |
| `fecha_fin`           | `VARCHAR` | 📅 Fecha de fin del contrato (ISO 8601)      |
| `moneda`              | `VARCHAR` | 💱 Código de moneda (e.g. `USD`, `EUR`, `COP`) |
| `pdf_url`             | `VARCHAR` | 🔗 URL del PDF almacenado (UploadThing CDN)  |

---

## 🚀 Instalación Local

### ✅ Prerrequisitos

- 🐍 Python 3.10+
- 🐘 Una base de datos PostgreSQL activa (local o en [Neon](https://neon.tech))
- 🔑 API Key de [OpenRouter](https://openrouter.ai)

### 1. 📥 Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/megumin-estate-ai.git
cd megumin-estate-ai
```

### 2. 🐍 Crear y activar entorno virtual

```bash
# Crear entorno
python -m venv venv

# Activar en Windows
venv\Scripts\activate

# Activar en macOS/Linux
source venv/bin/activate
```

### 3. 📦 Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. 🔐 Configurar variables de entorno

Copia el archivo de ejemplo y completa los valores:

```bash
cp .env.example .env
```

Edita `.env` con tus credenciales:

```env
DATABASE_URL=postgresql://usuario:password@host/nombre_db
OPENROUTER_API_KEY=sk-or-v1-...
```

### 5. 🗄️ Inicializar la base de datos

El esquema se crea automáticamente al arrancar la aplicación. Si necesitas resetear la base de datos en desarrollo:

```bash
python reset_db.py
```

### 6. ▶️ Levantar el servidor

```bash
uvicorn main:app --reload
```

La API quedará disponible en `http://localhost:8000`.  
La documentación interactiva (Swagger UI) en `http://localhost:8000/docs`. 📖

---

## ☁️ Despliegue en Producción

El backend está configurado para desplegarse en **[Render](https://render.com)**.

**⚡ Comando de inicio recomendado:**

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

Asegúrate de configurar las variables de entorno `DATABASE_URL` y `OPENROUTER_API_KEY` en el dashboard de Render antes del primer deploy.

---

## 🔐 Variables de Entorno

| Variable             | Requerida | Descripción                                                     |
|----------------------|-----------|-----------------------------------------------------------------|
| `DATABASE_URL`       | ✅ Sí     | Cadena de conexión PostgreSQL (formato SQLAlchemy)              |
| `OPENROUTER_API_KEY` | ✅ Sí     | API Key de OpenRouter para acceso al modelo LLM                 |

---

<div align="center">

✨ **Megumin Estate AI** — Construido con FastAPI · PostgreSQL · OpenRouter ✨

</div>
