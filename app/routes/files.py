from flask import Blueprint, jsonify, render_template, request

from app import storage
from app.calculations import aggregate_digit_counts, count_digits

files_bp = Blueprint('files_bp', __name__)


@files_bp.route('/files')
def files_page():
    return render_template('files.html')


@files_bp.route('/api/files')
def list_files():
    page = max(1, request.args.get('page', 1, type=int))
    per_page = max(1, request.args.get('per_page', 20, type=int))
    sort_dir = request.args.get('sort', 'desc')

    rows, total = storage.get_files_page(page, per_page, sort_dir)
    return jsonify({'files': rows, 'total': total, 'page': page, 'per_page': per_page})


@files_bp.route('/api/files/all-names')
def all_names():
    return jsonify({'names': storage.get_all_names()})


@files_bp.route('/api/files/calculate', methods=['POST'])
def calculate():
    data = request.get_json(force=True) or {}
    names = data.get('files', [])

    content_map = storage.get_files_content(names)

    per_file = {name: count_digits(content) for name, content in content_map.items()}
    total = aggregate_digit_counts(per_file)

    return jsonify({'total': total, 'per_file': per_file})
