from __future__ import annotations

import os
from collections import OrderedDict
from datetime import datetime
from functools import wraps

from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.utils import secure_filename

from detection import detect_all_directions
from image_utils import pick_latest_direction_image, pick_random_direction_image
from traffic_logic import decide_signal, normalize_direction_name


app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "traffic-ai-dev-secret")
app.config["LOGIN_USERNAME"] = os.environ.get("TRAFFIC_LOGIN_USERNAME", "admin")
app.config["LOGIN_PASSWORD"] = os.environ.get("TRAFFIC_LOGIN_PASSWORD", "admin123")


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
IMAGE_DIR = os.path.join(BASE_DIR, "static", "images")
UPLOAD_DIR = os.path.join(BASE_DIR, "static", "upload")
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

INPUT_IMAGES = OrderedDict(
    [
        ("North", "north"),
        ("South", "south"),
        ("East", "east"),
        ("West", "west"),
    ]
)


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get("authenticated"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped_view

def path_to_static_url(relative_path: str | None) -> str | None:
    if not relative_path:
        return None
    normalized = relative_path.replace("\\", "/")
    if "static/" not in normalized:
        return None
    return url_for("static", filename=normalized.split("static/", 1)[1])


def _allowed_file(filename: str) -> bool:
    _, ext = os.path.splitext(filename.lower())
    return ext in ALLOWED_IMAGE_EXTENSIONS


def build_dashboard_data(show_uploaded_once: bool = False):
    resolved_images = OrderedDict()

    for direction, stem in INPUT_IMAGES.items():
        resolved_path = None
        if show_uploaded_once:
            uploaded_path = pick_latest_direction_image(UPLOAD_DIR, stem)
            resolved_path = uploaded_path
        if resolved_path is None:
            resolved_path = pick_random_direction_image(IMAGE_DIR, stem)
        if resolved_path is None:
            resolved_images[direction] = os.path.join("static", "images", f"{stem}.jpg")
        else:
            resolved_images[direction] = os.path.relpath(resolved_path, BASE_DIR).replace("\\", "/")

    detections = detect_all_directions(resolved_images)
    counts = OrderedDict(
        (normalize_direction_name(item.direction), item.vehicle_count)
        for item in detections
    )
    emergency_counts = OrderedDict(
        (normalize_direction_name(item.direction), item.emergency_count)
        for item in detections
        if item.emergency_count > 0
    )
    decision = decide_signal(counts, emergency_counts=emergency_counts)

    details = []
    for item in detections:
        static_filename = item.image_path.replace("\\", "/") if os.path.exists(os.path.join(BASE_DIR, item.image_path)) else None
        details.append(
            {
                "direction": item.direction,
                "vehicle_count": item.vehicle_count,
                "class_counts": item.class_counts,
                "emergency_count": item.emergency_count,
                "emergency_labels": item.emergency_labels,
                "image_path": path_to_static_url(static_filename),
                "selected_image": os.path.basename(item.image_path) if static_filename else None,
                "error": item.error,
                "is_green": item.direction.upper() == decision.green_direction,
                "is_emergency": item.emergency_count > 0,
            }
        )

    return details, decision


def save_uploaded_images() -> None:
    """Save one uploaded image per direction into static/upload."""
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    saved_count = 0

    for direction, stem in INPUT_IMAGES.items():
        file_storage = request.files.get(stem)
        if not file_storage or not file_storage.filename:
            continue

        filename = secure_filename(file_storage.filename)
        if not _allowed_file(filename):
            flash(f"Skipped {direction} because the selected file format is not supported.", "warning")
            continue

        _, ext = os.path.splitext(filename)
        output_name = f"{stem}_{timestamp}{ext.lower()}"
        output_path = os.path.join(UPLOAD_DIR, output_name)
        file_storage.save(output_path)
        saved_count += 1

    if saved_count > 0:
        flash("Uploaded direction images successfully.", "success")
    else:
        flash("No valid direction images were uploaded.", "warning")


def cleanup_uploaded_images() -> None:
    """Remove uploaded images after they have been shown once."""
    if not os.path.isdir(UPLOAD_DIR):
        return

    for filename in os.listdir(UPLOAD_DIR):
        lower_name = filename.lower()
        if not lower_name.endswith(tuple(ALLOWED_IMAGE_EXTENSIONS)):
            continue
        if not any(lower_name.startswith(prefix) for prefix in (f"{stem}_" for stem in INPUT_IMAGES.values())):
            continue

        file_path = os.path.join(UPLOAD_DIR, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)


@app.route("/", methods=["GET"])
@login_required
def index():
    if session.pop("cleanup_uploaded_next_request", False):
        cleanup_uploaded_images()

    show_uploaded_once = session.pop("show_uploaded_once", False)
    details, decision = build_dashboard_data(show_uploaded_once=show_uploaded_once)
    max_count = max((item["vehicle_count"] for item in details), default=0)
    safe_max_count = max(max_count, 1)

    for item in details:
        item["bar_width"] = max(12, int((item["vehicle_count"] / safe_max_count) * 100))

    if show_uploaded_once:
        session["cleanup_uploaded_next_request"] = True

    return render_template(
        "index.html",
        details=details,
        decision=decision,
        total_vehicles=sum(item["vehicle_count"] for item in details),
        max_count=max_count,
        username=session.get("username", "Guest"),
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("authenticated"):
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if (
            username == app.config["LOGIN_USERNAME"]
            and password == app.config["LOGIN_PASSWORD"]
        ):
            session["authenticated"] = True
            session["username"] = username
            flash("Welcome back. You are now signed in.", "success")
            return redirect(url_for("index"))

        flash("Invalid username or password.", "warning")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "success")
    return redirect(url_for("login"))


@app.route("/upload", methods=["POST"])
@login_required
def upload_images():
    save_uploaded_images()
    session["show_uploaded_once"] = True
    return redirect(url_for("index"))


if __name__ == "__main__":
    os.makedirs(IMAGE_DIR, exist_ok=True)
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    app.run(debug=True)
