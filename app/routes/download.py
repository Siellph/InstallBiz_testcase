from flask import Blueprint, current_app, jsonify, render_template

from app import download_service

download_bp = Blueprint('download_bp', __name__)


@download_bp.route('/')
def index():
    return render_template('download.html')


@download_bp.route('/api/download/start', methods=['POST'])
def start_download():
    started = download_service.start_download(
        base_url=current_app.config['EXTERNAL_API_BASE_URL'],
        candidate_id=current_app.config['CANDIDATE_ID'],
        tz_name=current_app.config['DISPLAY_TIMEZONE'],
    )
    return jsonify({'started': started})


@download_bp.route('/api/download/status')
def download_status():
    return jsonify(download_service.get_state())
