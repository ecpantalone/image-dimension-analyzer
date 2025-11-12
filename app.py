#!/usr/bin/env python3
"""
Flask Web UI for Image Dimension Analyzer
"""

import os
import json
import threading
import uuid
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, session
from werkzeug.utils import secure_filename
import tempfile
import shutil

# Import our image analysis functions
from analyze_images import (
    process_images,
    save_results,
    DEFAULT_TARGET_DIMENSION
)

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'

# Store analysis jobs
analysis_jobs = {}

class AnalysisJob:
    def __init__(self, job_id, directory, target_dimension, mode, workers):
        self.job_id = job_id
        self.directory = directory
        self.target_dimension = target_dimension
        self.mode = mode
        self.workers = workers
        self.status = 'pending'
        self.progress = 0
        self.total_images = 0
        self.matching_images = 0
        self.all_results_file = None
        self.matching_results_file = None
        self.error = None
        self.start_time = None
        self.end_time = None

    def to_dict(self):
        return {
            'job_id': self.job_id,
            'directory': str(self.directory),
            'target_dimension': self.target_dimension,
            'mode': self.mode,
            'status': self.status,
            'progress': self.progress,
            'total_images': self.total_images,
            'matching_images': self.matching_images,
            'all_results_file': self.all_results_file,
            'matching_results_file': self.matching_results_file,
            'error': self.error,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None
        }

def run_analysis(job):
    """Run the image analysis in a background thread"""
    try:
        job.status = 'running'
        job.start_time = datetime.now()
        
        # Run the analysis
        all_results, matching_results = process_images(
            Path(job.directory),
            job.target_dimension,
            job.workers,
            job.mode
        )
        
        job.total_images = len(all_results)
        job.matching_images = len(matching_results)
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path('analysis_results')
        output_dir.mkdir(exist_ok=True)
        
        all_results_file = output_dir / f"web_analysis_all_{timestamp}.csv"
        matching_results_file = output_dir / f"web_analysis_{job.target_dimension}px_{timestamp}.csv"
        
        save_results(all_results, str(all_results_file))
        save_results(matching_results, str(matching_results_file))
        
        job.all_results_file = str(all_results_file)
        job.matching_results_file = str(matching_results_file)
        
        job.status = 'completed'
        job.progress = 100
        job.end_time = datetime.now()
        
    except Exception as e:
        job.status = 'error'
        job.error = str(e)
        job.end_time = datetime.now()

@app.route('/')
def index():
    """Render the main UI"""
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    """Start a new analysis job"""
    data = request.json
    
    directory = data.get('directory', '.')
    target_dimension = int(data.get('dimension', DEFAULT_TARGET_DIMENSION))
    mode = data.get('mode', 'lte')
    workers = int(data.get('workers', 4))
    
    # Validate directory
    dir_path = Path(directory)
    if not dir_path.exists():
        return jsonify({'error': f'Directory {directory} does not exist'}), 400
    if not dir_path.is_dir():
        return jsonify({'error': f'{directory} is not a directory'}), 400
    
    # Create job
    job_id = str(uuid.uuid4())
    job = AnalysisJob(job_id, directory, target_dimension, mode, workers)
    analysis_jobs[job_id] = job
    
    # Start analysis in background thread
    thread = threading.Thread(target=run_analysis, args=(job,))
    thread.start()
    
    return jsonify({'job_id': job_id, 'status': 'started'})

@app.route('/status/<job_id>')
def get_status(job_id):
    """Get the status of an analysis job"""
    job = analysis_jobs.get(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    return jsonify(job.to_dict())

@app.route('/download/<job_id>/<file_type>')
def download_results(job_id, file_type):
    """Download result files"""
    job = analysis_jobs.get(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    if job.status != 'completed':
        return jsonify({'error': 'Job not completed'}), 400
    
    if file_type == 'all':
        file_path = job.all_results_file
    elif file_type == 'matching':
        file_path = job.matching_results_file
    else:
        return jsonify({'error': 'Invalid file type'}), 400
    
    if not file_path or not Path(file_path).exists():
        return jsonify({'error': 'File not found'}), 404
    
    return send_file(file_path, as_attachment=True)

@app.route('/browse')
def browse_directory():
    """Browse directories on the server"""
    path = request.args.get('path', '.')
    try:
        path = Path(path).resolve()
        
        # Security: Don't allow access outside current directory in production
        # You may want to configure allowed directories
        
        items = []
        if path != Path('/').resolve():
            items.append({
                'name': '..',
                'path': str(path.parent),
                'type': 'directory'
            })
        
        for item in sorted(path.iterdir()):
            if item.is_dir():
                items.append({
                    'name': item.name,
                    'path': str(item),
                    'type': 'directory'
                })
        
        return jsonify({
            'current_path': str(path),
            'items': items
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/recent')
def get_recent_analyses():
    """Get list of recent analysis jobs"""
    recent_jobs = []
    for job_id, job in analysis_jobs.items():
        job_dict = job.to_dict()
        recent_jobs.append(job_dict)
    
    # Sort by start time (most recent first)
    recent_jobs.sort(key=lambda x: x['start_time'] or '', reverse=True)
    
    return jsonify(recent_jobs[:10])  # Return last 10 jobs

if __name__ == '__main__':
    # Create results directory
    Path('analysis_results').mkdir(exist_ok=True)
    
    port = 5001  # Using 5001 to avoid conflict with AirPlay on macOS
    print("Starting Image Dimension Analyzer Web UI...")
    print(f"Open http://localhost:{port} in your browser")
    app.run(debug=True, port=port, host='0.0.0.0')