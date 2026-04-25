# AI-Based Traffic Management System

This project simulates a smart traffic signal using AI-based vehicle detection and dynamic timing, without IoT hardware.

## Features

- Processes four direction images: North, South, East, and West
- Uses YOLOv8 via Ultralytics to detect vehicles
- Counts cars, motorcycles, buses, and trucks
- Selects the busiest direction and assigns the green signal
- Calculates green time with:

```text
green_time = 10 + (vehicle_count * 2)
```

- Flask web dashboard with automatic refresh
- Emergency-vehicle override:
  - If YOLO detects `ambulance`, `fire truck`, `firetruck`, or similar emergency labels, that direction gets immediate green priority
- Top-right upload button:
  - Lets you add new images directly into `static/upload/`
  - New files should still start with a direction prefix like `north`, `south`, `east`, or `west`

## Project Structure

```text
project/
  app.py
  detection.py
  traffic_logic.py
  image_utils.py
  requirements.txt
  templates/
    index.html
  static/
    images/
    upload/
```

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Add your input images in `static/images/` for Default Mode:

- You can keep multiple images for each direction
- Use filenames that start with the direction name, for example:
  - `north.jpg`, `north_1.jpeg`, `north_day.png`
  - `south.jpg`, `south_1.jpeg`
  - `east.jpg`, `east_2.png`
  - `west.jpg`, `west_1.webp`
- The dashboard randomly picks one matching image per direction on every refresh

4. Run the Flask app:

```bash
python app.py
```

5. Open the app in your browser:

```text
http://127.0.0.1:5000/
```

6. Sign in on the login page:

- Username: `admin`
- Password: `admin123`
- You can override them with:
  - `TRAFFIC_LOGIN_USERNAME`
  - `TRAFFIC_LOGIN_PASSWORD`

## Notes

- The first run may download the `yolov8n.pt` model automatically.
- If a direction has no matching images, the dashboard will show a clear error message for that direction.
- Important: the default COCO `yolov8n.pt` model does not include `ambulance` or `fire truck` classes. To detect them reliably, use custom-trained YOLO weights that include those labels.

## Optional Improvements

- Replace the browser auto-refresh with AJAX polling for smoother updates
- Display a chart for traffic density per direction
