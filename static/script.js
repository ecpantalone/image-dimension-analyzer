let currentJobId = null;
let currentPath = '.';
let pollInterval = null;

const analysisForm = document.getElementById('analysisForm');
const browseBtn = document.getElementById('browseBtn');
const browserModal = document.getElementById('browserModal');
const progressSection = document.getElementById('progressSection');
const resultsSection = document.getElementById('resultsSection');
const directoryInput = document.getElementById('directory');

document.addEventListener('DOMContentLoaded', () => {
    loadRecentAnalyses();
    setupEventListeners();
});

function setupEventListeners() {
    analysisForm.addEventListener('submit', handleFormSubmit);
    
    browseBtn.addEventListener('click', openBrowser);
    
    document.querySelector('.close-btn').addEventListener('click', closeBrowser);
    document.getElementById('cancelBrowseBtn').addEventListener('click', closeBrowser);
    document.getElementById('selectDirBtn').addEventListener('click', selectDirectory);
    
    document.getElementById('downloadAll').addEventListener('click', () => downloadResults('all'));
    document.getElementById('downloadMatching').addEventListener('click', () => downloadResults('matching'));
    document.getElementById('downloadErrorLog').addEventListener('click', downloadErrorLog);
}

async function handleFormSubmit(e) {
    e.preventDefault();
    
    const formData = {
        directory: document.getElementById('directory').value,
        dimension: parseInt(document.getElementById('dimension').value),
        mode: document.getElementById('mode').value,
        workers: parseInt(document.getElementById('workers').value)
    };
    
    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            currentJobId = data.job_id;
            startProgressTracking();
        } else {
            showError(data.error || 'Failed to start analysis');
        }
    } catch (error) {
        showError('Network error: ' + error.message);
    }
}

function startProgressTracking() {
    progressSection.classList.remove('hidden');
    resultsSection.classList.add('hidden');
    
    updateProgress({
        status: 'running',
        progress: 0
    });
    
    pollInterval = setInterval(checkProgress, 1000);
}

async function checkProgress() {
    if (!currentJobId) return;
    
    try {
        const response = await fetch(`/status/${currentJobId}`);
        const data = await response.json();
        
        updateProgress(data);
        
        if (data.status === 'completed') {
            clearInterval(pollInterval);
            showResults(data);
            loadRecentAnalyses();
        } else if (data.status === 'error') {
            clearInterval(pollInterval);
            showError(`Analysis failed: ${data.error}`);
            progressSection.classList.add('hidden');
        }
    } catch (error) {
        console.error('Error checking progress:', error);
    }
}

function updateProgress(data) {
    const statusText = document.getElementById('statusText');
    const progressFill = document.getElementById('progressFill');
    const statsText = document.getElementById('statsText');
    
    if (data.status === 'running') {
        statusText.textContent = 'Analyzing images...';
    } else if (data.status === 'pending') {
        statusText.textContent = 'Initializing...';
    } else if (data.status === 'completed') {
        statusText.textContent = 'Analysis complete!';
    }
    
    if (data.progress !== undefined) {
        progressFill.style.width = `${data.progress}%`;
        progressFill.textContent = `${Math.round(data.progress)}%`;
    }
    
    if (data.total_images > 0) {
        statsText.textContent = `Found ${data.total_images} images, ${data.matching_images} match criteria`;
    }
}

function showResults(data) {
    progressSection.classList.add('hidden');
    resultsSection.classList.remove('hidden');
    
    document.getElementById('totalImages').textContent = data.total_images;
    document.getElementById('matchingImages').textContent = data.matching_images;
    
    const matchRate = data.total_images > 0 
        ? Math.round((data.matching_images / data.total_images) * 100) 
        : 0;
    document.getElementById('matchRate').textContent = `${matchRate}%`;
}

async function downloadResults(type) {
    if (!currentJobId) return;
    
    window.location.href = `/download/${currentJobId}/${type}`;
}

async function downloadErrorLog() {
    try {
        const response = await fetch('/download-errors');
        
        if (response.ok) {
            // Trigger download
            window.location.href = '/download-errors';
        } else {
            const data = await response.json();
            showError(data.error || 'Failed to download error log');
        }
    } catch (error) {
        showError('Network error: ' + error.message);
    }
}

async function openBrowser() {
    browserModal.classList.remove('hidden');
    await loadDirectory(currentPath);
}

function closeBrowser() {
    browserModal.classList.add('hidden');
}

async function loadDirectory(path) {
    try {
        const response = await fetch(`/browse?path=${encodeURIComponent(path)}`);
        const data = await response.json();
        
        if (response.ok) {
            currentPath = data.current_path;
            displayDirectory(data);
        } else {
            showError('Failed to load directory');
        }
    } catch (error) {
        showError('Failed to browse directory');
    }
}

function displayDirectory(data) {
    const currentPathEl = document.getElementById('currentPath');
    const directoryList = document.getElementById('directoryList');
    
    currentPathEl.textContent = data.current_path;
    directoryList.innerHTML = '';
    
    data.items.forEach(item => {
        const div = document.createElement('div');
        div.className = 'directory-item';
        div.textContent = item.name;
        div.onclick = () => {
            if (item.type === 'directory') {
                loadDirectory(item.path);
            }
        };
        directoryList.appendChild(div);
    });
}

function selectDirectory() {
    directoryInput.value = currentPath;
    closeBrowser();
}

async function loadRecentAnalyses() {
    try {
        const response = await fetch('/recent');
        const analyses = await response.json();
        
        const container = document.getElementById('recentAnalyses');
        
        if (analyses.length === 0) {
            container.innerHTML = '<p class="loading">No recent analyses</p>';
            return;
        }
        
        container.innerHTML = analyses.map(analysis => {
            const date = analysis.start_time ? new Date(analysis.start_time).toLocaleString() : 'Unknown';
            const statusClass = `status-${analysis.status}`;
            
            return `
                <div class="analysis-item">
                    <div class="analysis-info">
                        <h4>${analysis.directory}</h4>
                        <div class="analysis-meta">
                            <span>Dimension: ${analysis.target_dimension}px</span>
                            <span>Mode: ${analysis.mode}</span>
                            <span>${date}</span>
                        </div>
                    </div>
                    <span class="analysis-status ${statusClass}">${analysis.status}</span>
                </div>
            `;
        }).join('');
    } catch (error) {
        console.error('Failed to load recent analyses:', error);
    }
}

function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error';
    errorDiv.textContent = message;
    
    analysisForm.parentElement.insertBefore(errorDiv, analysisForm.nextSibling);
    
    setTimeout(() => errorDiv.remove(), 5000);
}

function showSuccess(message) {
    const successDiv = document.createElement('div');
    successDiv.className = 'success';
    successDiv.textContent = message;
    
    analysisForm.parentElement.insertBefore(successDiv, analysisForm.nextSibling);
    
    setTimeout(() => successDiv.remove(), 5000);
}

setInterval(loadRecentAnalyses, 10000);