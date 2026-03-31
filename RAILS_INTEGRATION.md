# Manga Bubble Detector — Rails Integration Guide

Base URL: `https://manga-bubble-detector-py-production.up.railway.app`

---

## What it does

Takes a manga page image (via URL or file upload) and returns the locations of all detected text overlay regions as bounding boxes — in both pixel coordinates and percentages.

---

## Endpoints

### `GET /health`

Quick check that the service is up.

```
GET /health
```

```json
{ "status": "ok", "model_loaded": true }
```

---

### `POST /predict/url`

Pass an image URL (e.g. from S3) and get back all detected boxes.

**Request**

```
POST /predict/url
Content-Type: application/json
```

```json
{
  "image_url": "https://your-bucket.s3.amazonaws.com/chapters/36/images/abc123.jpg",
  "confidence": 0.25
}
```

| Field        | Type   | Required | Default | Notes                                    |
|--------------|--------|----------|---------|------------------------------------------|
| `image_url`  | string | yes      | —       | Must be publicly accessible              |
| `confidence` | float  | no       | `0.25`  | Lower = more boxes, higher = fewer/surer |

**Response**

```json
{
  "count": 9,
  "image_width": 856,
  "image_height": 1222,
  "boxes": [
    {
      "x1": 689.05,
      "y1": 79.9,
      "x2": 796.58,
      "y2": 318.05,
      "x_pct": 80.5,
      "y_pct": 6.54,
      "width_pct": 12.56,
      "height_pct": 19.49,
      "confidence": 0.8942
    }
  ]
}
```

| Field         | Description                                                        |
|---------------|--------------------------------------------------------------------|
| `x1, y1`      | Top-left corner in pixels                                          |
| `x2, y2`      | Bottom-right corner in pixels                                      |
| `x_pct`       | Left edge as % of image width — matches existing overlay format    |
| `y_pct`       | Top edge as % of image height — matches existing overlay format    |
| `width_pct`   | Box width as % of image width — matches existing overlay format    |
| `height_pct`  | Box height as % of image height — matches existing overlay format  |
| `confidence`  | Model confidence 0.0–1.0                                           |

The `_pct` fields map directly to `shape.x`, `shape.y`, `shape.width`, `shape.height` in your existing overlay JSON.

---

### `POST /predict/upload`

Upload an image file directly instead of passing a URL.

```
POST /predict/upload
Content-Type: multipart/form-data
```

| Field        | Type  | Required | Default |
|--------------|-------|----------|---------|
| `file`       | file  | yes      | —       |
| `confidence` | float | no       | `0.25`  |

Response is the same shape as `/predict/url`.

---

## Rails example

```ruby
# Gemfile
gem "faraday"
```

```ruby
# app/services/bubble_detector_service.rb
class BubbleDetectorService
  BASE_URL = "https://manga-bubble-detector-py-production.up.railway.app"

  def self.detect(image_url, confidence: 0.25)
    conn = Faraday.new(BASE_URL) do |f|
      f.request :json
      f.response :json
      f.options.timeout = 30
    end

    response = conn.post("/predict/url", {
      image_url: image_url,
      confidence: confidence
    })

    response.body
  end
end
```

**Usage**

```ruby
result = BubbleDetectorService.detect("https://your-s3-url.jpg")

result["count"]   # => 9
result["boxes"]   # => array of box hashes

# Map to your overlay shape format
suggested_overlays = result["boxes"].map do |box|
  {
    shape: {
      x:      box["x_pct"],
      y:      box["y_pct"],
      width:  box["width_pct"],
      height: box["height_pct"]
    },
    confidence: box["confidence"]
  }
end
```

---

## Notes

- Boxes are sorted by confidence (highest first)
- Typical response time is 1–3 seconds (CPU inference)
- The service may have a ~5–10 second cold start if it hasn't been hit recently (Railway free tier sleep)
- If you want to filter out low-confidence detections, raise `confidence` to `0.5` or higher
