# Manga Bubble Detector API

FastAPI service that detects text overlay regions in manga pages using a YOLOv8 model trained on your annotated chapter data.

---

## Setup

1. Copy your trained model into this directory:
   ```
   cp /opt/homebrew/runs/detect/runs/bubble_detector/weights/best.pt .
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Start the server:
   ```
   uvicorn main:app --reload --port 8000
   ```

Interactive docs available at `http://localhost:8000/docs`.

---

## Endpoints

### `GET /health`

Returns whether the service is running and the model is loaded.

**Response**
```json
{
  "status": "ok",
  "model_loaded": true
}
```

---

### `POST /predict/url`

Run detection on an image fetched from a URL (e.g. an S3 link). This is the recommended endpoint when your images are already hosted.

**Request body** `application/json`

| Field        | Type   | Required | Default | Description                              |
|--------------|--------|----------|---------|------------------------------------------|
| `image_url`  | string | yes      | —       | Publicly accessible URL to a JPG or PNG  |
| `confidence` | float  | no       | `0.25`  | Minimum confidence threshold (0.0 – 1.0) |

**Example request**
```json
{
  "image_url": "https://expressfeel.s3.amazonaws.com/chapters/36/images/f495e5c7.jpg",
  "confidence": 0.25
}
```

**Example response**
```json
{
  "count": 7,
  "image_width": 728,
  "image_height": 1096,
  "boxes": [
    {
      "x1": 377.14,
      "y1": 587.02,
      "x2": 485.33,
      "y2": 719.88,
      "x_pct": 51.8,
      "y_pct": 53.56,
      "width_pct": 14.86,
      "height_pct": 12.12,
      "confidence": 0.9823
    }
  ]
}
```

---

### `POST /predict/upload`

Run detection on a directly uploaded image file. Useful for testing or when you have the image locally.

**Request** `multipart/form-data`

| Field        | Type  | Required | Default | Description                              |
|--------------|-------|----------|---------|------------------------------------------|
| `file`       | file  | yes      | —       | Image file (JPG, JPEG, PNG)              |
| `confidence` | float | no       | `0.25`  | Minimum confidence threshold (0.0 – 1.0) |

**Example (curl)**
```bash
curl -X POST http://localhost:8000/predict/upload \
  -F "file=@page.jpg" \
  -F "confidence=0.25"
```

**Response** — same shape as `/predict/url`.

---

## Response fields explained

| Field          | Description                                                   |
|----------------|---------------------------------------------------------------|
| `count`        | Number of boxes detected                                      |
| `image_width`  | Width of the image in pixels                                  |
| `image_height` | Height of the image in pixels                                 |
| `boxes`        | Array of detected regions                                     |
| `x1, y1`       | Top-left corner in pixels                                     |
| `x2, y2`       | Bottom-right corner in pixels                                 |
| `x_pct`        | Left edge as % of image width (matches your JSON overlay format) |
| `y_pct`        | Top edge as % of image height (matches your JSON overlay format) |
| `width_pct`    | Box width as % of image width                                 |
| `height_pct`   | Box height as % of image height                               |
| `confidence`   | Model confidence score (0.0 – 1.0)                           |

The `_pct` fields match your existing overlay JSON format so you can drop them directly into your overlay structure without conversion.

---

## Calling from Rails

```ruby
require "net/http"
require "json"

def detect_bubbles(image_url, confidence: 0.25)
  uri = URI("https://your-service.railway.app/predict/url")
  response = Net::HTTP.post(
    uri,
    { image_url: image_url, confidence: confidence }.to_json,
    "Content-Type" => "application/json"
  )
  JSON.parse(response.body)
end
```
