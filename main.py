from fastapi import FastAPI, UploadFile, File
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from rembg import remove, new_session
from PIL import Image
import io

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variable global para inicializar solo bajo demanda (ahorra memoria al arrancar)
session = None

def get_session():
    global session
    if session is None:
        # 'u2netp' es la versión compacta (solo 4 MB de modelo y ~120 MB de RAM)
        session = new_session("u2netp")
    return session

@app.get("/")
def home():
    return {"status": "online"}

@app.post("/remove-bg")
async def remove_background(image_file: UploadFile = File(...)):
    contents = await image_file.read()
    input_image = Image.open(io.BytesIO(contents)).convert("RGBA")

    # Redimensionar ligeramente si la imagen es gigantesca para no saturar los 512 MB de Render
    max_dimension = 1600
    if max(input_image.size) > max_dimension:
        input_image.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)

    # Recorte con alpha_matting ligero
    sess = get_session()
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

    return Response(content=img_byte_arr.getvalue(), media_type="image/png")
