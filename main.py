from fastapi import FastAPI, UploadFile, File
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from rembg import remove, new_session
from PIL import Image
import io

app = FastAPI()

# Permitir que tu frontend en Netlify pueda comunicarse con la API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelo de alta definición para productos y tapas claras (IS-Net)
session = new_session("isnet-general-use")

@app.post("/remove-bg")
async def remove_background(image_file: UploadFile = File(...)):
    contents = await image_file.read()
    input_image = Image.open(io.BytesIO(contents)).convert("RGBA")

    # Recorte semántico con preservación de bordes y transparencias
    output_image = remove(
        input_image,
        session=session,
        alpha_matting=True,
        alpha_matting_foreground_threshold=240,
        alpha_matting_background_threshold=15,
        alpha_matting_erode_size=8
    )

    img_byte_arr = io.BytesIO()
    output_image.save(img_byte_arr, format="PNG")
    img_byte_arr.seek(0)

    return Response(content=img_byte_arr.getvalue(), media_type="image/png")
