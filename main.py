import io
import httpx
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from PIL import Image
from ultralytics import YOLO

MODEL_PATH = Path("best.pt")
model: YOLO | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global model
    if not MODEL_PATH.exists():
        raise RuntimeError(f"Model not found at {MODEL_PATH}. See README.")
    model = YOLO(str(MODEL_PATH))
    print("Model loaded.")
    yield
    model = None


app = FastAPI(
    title="Manga Bubble Detector",
    description="Detects text overlay regions in manga pages using YOLOv8.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class Box(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float
    x_pct: float
    y_pct: float
    width_pct: float
    height_pct: float
    confidence: float


class PredictResponse(BaseModel):
    boxes: list[Box]
    count: int
    image_width: int
    image_height: int


class UrlRequest(BaseModel):
    image_url: HttpUrl
    confidence: float = 0.25


def run_inference(pil_image: Image.Image, confidence: float) -> PredictResponse:
    img_w, img_h = pil_image.size
    results = model.predict(source=pil_image, imgsz=1024, conf=confidence, verbose=False)
    r = results[0]

    boxes = []
    for b in r.boxes:
        x1, y1, x2, y2 = [v.item() for v in b.xyxy[0]]
        conf = b.conf[0].item()
        w = x2 - x1
        h = y2 - y1
        boxes.append(Box(
            x1=round(x1, 2),
            y1=round(y1, 2),
            x2=round(x2, 2),
            y2=round(y2, 2),
            x_pct=round(x1 / img_w * 100, 4),
            y_pct=round(y1 / img_h * 100, 4),
            width_pct=round(w / img_w * 100, 4),
            height_pct=round(h / img_h * 100, 4),
            confidence=round(conf, 4),
        ))

    return PredictResponse(
        boxes=boxes,
        count=len(boxes),
        image_width=img_w,
        image_height=img_h,
    )


@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": model is not None}


@app.post("/predict/url", response_model=PredictResponse)
async def predict_from_url(body: UrlRequest):
    """Run detection on an image fetched from a URL (e.g. S3)."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(str(body.image_url))
            response.raise_for_status()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=422, detail=f"Failed to fetch image: {e}")

    try:
        pil_image = Image.open(io.BytesIO(response.content)).convert("RGB")
    except Exception:
        raise HTTPException(status_code=422, detail="Could not decode image from URL.")

    return run_inference(pil_image, body.confidence)


@app.post("/predict/upload", response_model=PredictResponse)
async def predict_from_upload(
    file: UploadFile = File(...),
    confidence: float = 0.25,
):
    """Run detection on an uploaded image file."""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=422, detail="File must be an image.")

    contents = await file.read()
    try:
        pil_image = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception:
        raise HTTPException(status_code=422, detail="Could not decode uploaded image.")

    return run_inference(pil_image, confidence)
