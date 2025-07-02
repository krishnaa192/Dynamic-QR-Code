from flask import Flask, request, redirect, render_template
from datetime import datetime
import os
import qrcode
from werkzeug.utils import secure_filename
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_sqlalchemy import SQLAlchemy

# ── imports ────────────────────────────────────────────────────────────
from flask import Flask, request, redirect, render_template, send_file
import io
import uuid
import qrcode
# …existing imports unchanged…

# ── download route ─────────────────────────────────────────────────────

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///qr_tracking.db"
app.config["SECRET_KEY"] = "any-secret-key"
db = SQLAlchemy(app)
admin = Admin(app, name="QR Dashboard", template_mode="bootstrap3")

# Models
class QRLink(db.Model):
    __tablename__ = "qr_links"
    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String, nullable=False)
    destination_url = db.Column(db.String, nullable=False)
    active = db.Column(db.Integer, default=1)

    scans = db.relationship("QRScan", back_populates="link", cascade="all, delete-orphan")


class QRScan(db.Model):
    __tablename__ = "qr_scans"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    qr_id = db.Column(db.String, db.ForeignKey("qr_links.id"), nullable=False)
    timestamp = db.Column(db.String)
    ip_address = db.Column(db.String)
    user_agent = db.Column(db.String)
    country = db.Column(db.String)
    region = db.Column(db.String)

    link = db.relationship("QRLink", back_populates="scans")


# Routes
@app.route("/")
def index():
    qr_links = QRLink.query.all()
    return render_template("index.html", qr_links=qr_links)

import requests

import requests

@app.route("/qr")
def handle_qr():
    qr_id = request.args.get("id")
    if not qr_id:
        return "Invalid QR code", 400

    link = QRLink.query.filter_by(id=qr_id, active=1).first()
    if not link:
        return "QR code not found or inactive", 404

    user_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    if user_ip == "127.0.0.1":
        user_ip = "103.120.179.33"  # use sample IP while developing

    # IP Geolocation
    try:
        geo = requests.get(f"https://ipapi.co/{user_ip}/json/").json()
        country = geo.get("country_name")
        region = geo.get("region")
    except:
        country = None
        region = None

    scan = QRScan(
        qr_id=qr_id,
        timestamp=datetime.now().isoformat(),
        ip_address=user_ip,
        user_agent=request.headers.get("User-Agent"),
        country=country,
        region=region
    )
    db.session.add(scan)
    db.session.commit()

    return redirect(link.destination_url)
import uuid



@app.route("/downloadQR")
def download_qr():
    qr_id = request.args.get("id")
    if not qr_id:
        return "Invalid QR code", 400

    link = QRLink.query.filter_by(id=qr_id, active=1).first()
    if not link:
        return "QR code not found or inactive", 404

    # Build a fresh QR image for the real destination URL
    # (alternatively, read the PNG you’ve already saved in /static/qr)
    img = qrcode.make(link.destination_url)          # or generate_qr_code(...)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    filename = f"{qr_id}.png"                      # nice, deterministic name
    return send_file(
        buf,
        mimetype="image/png",
        as_attachment=True,
        download_name=filename
    )




@app.route("/create", methods=["POST"])
def create_qr():
    name = request.form.get("name")
    url = request.form.get("url")
    if not name or not url:
        return "Missing data", 400

    # ✅ Generate unique QR ID
    qr_id = uuid.uuid4().hex[:6]

    qr_url = f"http://localhost:5000/qr?id={qr_id}"
    save_path = f"static/qr/{qr_id}.png"
    os.makedirs("static/qr", exist_ok=True)

    img = qrcode.make(qr_url)
    img.save(save_path)

    # ✅ Include id when inserting
    qr = QRLink(id=qr_id, name=name, destination_url=url, active=1)
    db.session.add(qr)
    db.session.commit()

    return redirect("/")

# Admin views
from flask_admin.contrib.sqla import ModelView

class QRLinkAdmin(ModelView):
    column_list = ("id", "name", "destination_url", "active")
    form_excluded_columns = ("scans",)
    column_searchable_list = ("name", "destination_url")
    column_filters = ("active",)


class QRScanAdmin(ModelView):
    column_list = ("id", "qr_id", "qr_name", "timestamp", "ip_address", "country", "region")
    column_labels = {"qr_name": "QR Name"}
    column_filters = ("qr_id", "link.name", "ip_address", "country", "region")
    column_searchable_list = ("qr_id", "ip_address", "country", "region")
    can_export = True

    def _qr_name_formatter(view, context, model, name):
        return model.link.name if model.link else "—"

    column_formatters = {
        "qr_name": _qr_name_formatter
    }


admin.add_view(QRLinkAdmin(QRLink, db.session, name="QR Codes"))
admin.add_view(QRScanAdmin(QRScan, db.session, name="QR Scans"))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
