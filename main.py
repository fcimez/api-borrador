from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import Response, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from rembg import remove, new_session
from PIL import Image
import io

app = FastAPI()

# 1. Configuración abierta de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# 2. Manejador manual de OPTIONS para preflight en navegadores
@app.options("/{rest_of_path:path}")
async def preflight_handler(rest_of_path: str):
    response = Response()
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

# Variable global para inicialización bajo demanda
session = None

def get_session():
    global session
    if session is None:
        # u2netp utiliza ~120MB de RAM (ideal para el límite de 512MB de Render)
        session = new_session("u2netp")
    return session

@app.get("/")
def home():
    return {"status": "online"}

@app.post("/remove-bg")
async def remove_background(image_file: UploadFile = File(...)):
    try:
        contents = await image_file.read()
        input_image = Image.open(io.BytesIO(contents)).convert("RGBA")

        # Redimensionar si es muy pesada para evitar que supere los 512MB de Render
        max_dim = 1200
        if max(input_image.size) > max_dim:
            input_image.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

        sess = get_session()
        
        # Procesamiento con rembg
        output_image = remove(
            input_image,
            session=sess,
            alpha_matting=True,
            alpha_matting_foreground_threshold=240,
            alpha_matting_background_threshold=15,
            alpha_matting_erode_size=5
        )

        img_byte_arr = io.BytesIO()
        output_image.save(img_byte_arr, format="PNG")
        img_byte_arr.seek(0)

        return Response(
            content=img_byte_arr.getvalue(),
            media_type="image/png",
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
                "Access-Control-Allow-Headers": "*"
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)},
            headers={"Access-Control-Allow-Origin": "*"}
        )
