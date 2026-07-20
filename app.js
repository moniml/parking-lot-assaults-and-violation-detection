// Application State
let currentSource = 'default'; // 'default' or 'upload'
let uploadFilePath = '';
let telemetryInterval = null;
let threatHistory = [];
const maxHistoryPoints = 50;

// Alarm & Audio Settings
let isSirenMuted = true;
const sirenSound = document.getElementById('siren-sound');

// DOM Elements
const landingSection = document.getElementById('landing-section');
const dashboardSection = document.getElementById('dashboard-section');
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const browseBtn = document.getElementById('browse-btn');
const stockStreamLink = document.getElementById('stock-stream-link');
const streamPlayer = document.getElementById('stream-player');
const streamLoader = document.getElementById('stream-loader');
const sourceNameDisplay = document.getElementById('source-name-display');
const threatBadge = document.getElementById('threat-badge');
const timeDisplay = document.getElementById('time-display');

// Telemetry Elements
const telFps = document.getElementById('tel-fps');
const telThreat = document.getElementById('tel-threat');
const telThreatBar = document.getElementById('tel-threat-bar');
const telObjects = document.getElementById('tel-objects');
const telStatus = document.getElementById('tel-status');

// Controls
const confSlider = document.getElementById('conf-slider');
const confVal = document.getElementById('conf-val');
const classToggles = document.querySelectorAll('.class-toggle');
const sirenToggleBtn = document.getElementById('siren-toggle-btn');
const changeSourceBtn = document.getElementById('change-source-btn');

// Terminal & Chart
const terminalLog = document.getElementById('terminal-log');
const threatChart = document.getElementById('threat-chart');
const chartCtx = threatChart.getContext('2d');

// Initialize Timeline History
for (let i = 0; i < maxHistoryPoints; i++) {
    threatHistory.push(0);
}

/* ==========================================================================
   1. UTILITIES & HELPER FUNCTIONS
   ========================================================================== */

// Format live surveillance timestamp: YYYY-MM-DD HH:MM:SS:MS
function updateSurveillanceTime() {
    const now = new Date();
    const pad = (num, size = 2) => ('00' + num).slice(-size);
    const ms = pad(Math.floor(now.getMilliseconds() / 10), 2);
    
    timeDisplay.textContent = 
        `${now.getFullYear()}-${pad(now.getMonth()+1)}-${pad(now.getDate())} ` +
        `${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}:${ms}`;
}
setInterval(updateSurveillanceTime, 30);

// Add event log to terminal
function addTerminalLog(text, type = 'system') {
    const now = new Date();
    const timestamp = `[${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}]`;
    
    const logEntry = document.createElement('div');
    logEntry.className = `log-entry ${type}-log`;
    
    let actionButtons = '';
    if (type !== 'system') {
        actionButtons = `
            <div class="log-actions">
                <button class="log-btn ack-btn" onclick="acknowledgeLog(this)">ACK</button>
                <button class="log-btn esc-btn" onclick="dispatchSecurity(this, '${type.toUpperCase()}')">DISPATCH</button>
            </div>
        `;
    }
    
    logEntry.innerHTML = `
        <span class="log-time">${timestamp}</span>
        <span class="log-text">${text}</span>
        ${actionButtons}
    `;
    
    terminalLog.appendChild(logEntry);
    
    // Auto scroll to bottom
    terminalLog.scrollTop = terminalLog.scrollHeight;
}

window.acknowledgeLog = function(btn) {
    const entry = btn.closest('.log-entry');
    entry.style.opacity = '0.5';
    entry.querySelector('.log-actions').innerHTML = '<span style="color: var(--neon-green); font-size:0.6rem; letter-spacing:1px;">RESOLVED</span>';
    addTerminalLog(`[RESOLVED] Threat event acknowledged by monitor console.`, 'system');
};

window.dispatchSecurity = function(btn, type) {
    const entry = btn.closest('.log-entry');
    entry.style.opacity = '0.7';
    entry.querySelector('.log-actions').innerHTML = '<span style="color: var(--neon-red); font-size:0.6rem; letter-spacing:1px;">DISPATCHED</span>';
    addTerminalLog(`[DISPATCH] SECURITY RESPONSE UNIT ACTIVATED. Tactical dispatch for ${type} in camera zone.`, 'violation');
};

/* ==========================================================================
   2. LANDING / FILE UPLOAD OPERATIONS
   ========================================================================== */

// Drag over/leave effects
dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('dragover');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleUpload(files[0]);
    }
});

// Click Browse triggers file input
browseBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    fileInput.click();
});

fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) {
        handleUpload(fileInput.files[0]);
    }
});

// Upload handler
function handleUpload(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    // Show spinner visual
    browseBtn.disabled = true;
    browseBtn.textContent = 'UPLOADING FOOTAGE...';
    
    fetch('/api/upload', {
        method: 'POST',
        body: formData
    })
    .then(async response => {
        const contentType = response.headers.get("content-type");
        const isJson = contentType && contentType.indexOf("application/json") !== -1;
        
        if (!response.ok) {
            let errMsg = `Server returned status ${response.status}`;
            if (isJson) {
                try {
                    const errData = await response.json();
                    errMsg = errData.message || errData.error || errMsg;
                } catch (e) {}
            } else {
                try {
                    const textHtml = await response.text();
                    console.error("Server HTML Error Page content:", textHtml);
                } catch (e) {}
            }
            throw new Error(errMsg);
        }
        
        if (!isJson) {
            throw new Error("Invalid response format (Expected JSON)");
        }
        
        return response.json();
    })
    .then(data => {
        browseBtn.disabled = false;
        browseBtn.textContent = 'BROWSE DIRECTORY';
        
        if (data.success) {
            currentSource = 'upload';
            uploadFilePath = data.filepath || (data.data && data.data.filepath);
            sourceNameDisplay.textContent = file.name;
            startSurveillance();
        } else {
            alert(`Upload failed: ${data.message || data.error}`);
        }
    })
    .catch(err => {
        browseBtn.disabled = false;
        browseBtn.textContent = 'BROWSE DIRECTORY';
        console.error("Upload error details:", err);
        alert(`Surveillance upload error: ${err.message || err}`);
    });
}

// Stock stream trigger
stockStreamLink.addEventListener('click', (e) => {
    e.preventDefault();
    currentSource = 'default';
    uploadFilePath = '';
    sourceNameDisplay.textContent = 'STOCK_STREAM.avi';
    startSurveillance();
});

/* ==========================================================================
   3. SURVEILLANCE DASHBOARD INITIALIZATION & STREAMING
   ========================================================================== */

function getStreamUrl() {
    const conf = confSlider.value;
    const classes = Array.from(classToggles)
        .filter(cb => cb.checked)
        .map(cb => cb.getAttribute('data-class'))
        .join(',');
        
    let url = `/api/stream?conf=${conf}&classes=${classes}`;
    if (currentSource === 'default') {
        url += '&source=default';
    } else {
        url += `&source=upload&path=${encodeURIComponent(uploadFilePath)}`;
    }
    return url;
}

function startSurveillance() {
    // Show dashboard, hide landing
    landingSection.classList.add('hidden');
    dashboardSection.classList.remove('hidden');
    
    // Show loading spinner in video window
    streamLoader.classList.remove('hidden');
    streamPlayer.style.opacity = '0';
    
    // Set stream player source
    const streamUrl = getStreamUrl();
    streamPlayer.src = streamUrl;
    
    // Once image begins to load, hide loading screen
    streamPlayer.onload = () => {
        streamLoader.classList.add('hidden');
        streamPlayer.style.opacity = '1';
    };
    
    addTerminalLog(`Initializing active stream source: ${sourceNameDisplay.textContent}`, 'system');
    addTerminalLog(`Establishing YOLO Inference pipeline connection...`, 'system');
    
    // Start polling telemetry
    if (telemetryInterval) clearInterval(telemetryInterval);
    telemetryInterval = setInterval(fetchTelemetry, 250);
    
    // Reset Chart timeline
    threatHistory = Array(maxHistoryPoints).fill(0);
}

function stopSurveillance() {
    // Reset video source
    streamPlayer.src = '';
    if (telemetryInterval) clearInterval(telemetryInterval);
    
    // Stop Siren
    sirenSound.pause();
    sirenSound.currentTime = 0;
    
    // Reset UI state
    landingSection.classList.remove('hidden');
    dashboardSection.classList.add('hidden');
    
    addTerminalLog(`Surveillance session terminated. Matrix offline.`, 'system');
}

changeSourceBtn.addEventListener('click', stopSurveillance);

/* ==========================================================================
   4. TELEMETRY & LIVE ALERTS HANDLING
   ========================================================================== */

let loggedThreats = new Set(); // Keep track of logged threat timestamps to avoid duplication

function fetchTelemetry() {
    fetch('/api/telemetry')
    .then(res => res.json())
    .then(data => {
        // Update stats widgets
        telFps.textContent = data.fps || 30;
        telThreat.textContent = `${data.threat_score}%`;
        telThreatBar.style.width = `${data.threat_score}%`;
        
        let objectCount = 0;
        if (data.active_counts) {
            objectCount = Object.values(data.active_counts).reduce((a, b) => a + b, 0);
        }
        telObjects.textContent = objectCount;
        telStatus.textContent = data.status.toUpperCase();
        
        // Threat severity badge update
        if (data.threat_score === 0) {
            threatBadge.textContent = 'SAFE';
            threatBadge.className = 'badge green-badge';
            telStatus.style.color = 'var(--neon-green)';
        } else if (data.threat_score < 40) {
            threatBadge.textContent = 'SUSPICIOUS';
            threatBadge.className = 'badge orange-badge';
            telStatus.style.color = 'var(--neon-orange)';
        } else if (data.threat_score < 75) {
            threatBadge.textContent = 'WARNING';
            threatBadge.className = 'badge red-alert-badge';
            telStatus.style.color = 'var(--neon-red)';
        } else {
            threatBadge.textContent = 'CRITICAL ALERT';
            threatBadge.className = 'badge red-alert-badge';
            threatBadge.style.boxShadow = '0 0 15px var(--neon-red-glow)';
            telStatus.style.color = '#ff0000';
        }
        
        // Log threats in terminal
        if (data.detections && data.detections.length > 0) {
            data.detections.forEach(det => {
                const threatKey = `${det.class}_${Math.floor(data.timestamp / 2)}`; // throttle duplicate logs (approx 2s window)
                if (det.class !== 'Normal' && !loggedThreats.has(threatKey)) {
                    loggedThreats.add(threatKey);
                    
                    let logType = 'suspicious';
                    if (det.class === 'Violation') logType = 'violation';
                    if (det.class === 'Assault') logType = 'assault';
                    
                    addTerminalLog(`DETECTION ALERT: ${det.class} detected with confidence ${Math.round(det.confidence * 100)}%`, logType);
                }
            });
        }
        
        // Siren triggering logic
        if (data.threat_score >= 70 && !isSirenMuted) {
            if (sirenSound.paused) {
                sirenSound.play().catch(e => console.log("Audio play blocked by browser sandbox: ", e));
            }
        } else {
            sirenSound.pause();
        }
        
        // Push to threat index timeline history
        threatHistory.push(data.threat_score);
        if (threatHistory.length > maxHistoryPoints) {
            threatHistory.shift();
        }
        
        // Render history chart
        renderThreatTimelineChart();
    })
    .catch(err => {
        console.error("Telemetry fetch error: ", err);
    });
}

// Clean log cache every 60s
setInterval(() => {
    loggedThreats.clear();
}, 60000);

// Siren manual mute toggle
sirenToggleBtn.addEventListener('click', () => {
    isSirenMuted = !isSirenMuted;
    if (isSirenMuted) {
        sirenSound.pause();
        sirenToggleBtn.innerHTML = `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="btn-icon">
                <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/>
                <path d="M19 10v1a7 7 0 0 1-14 0v-1"/>
                <line x1="12" y1="19" x2="12" y2="22"/>
            </svg>
            UNMUTE SYSTEM SIREN
        `;
        sirenToggleBtn.style.borderColor = 'var(--text-muted)';
        sirenToggleBtn.style.color = 'var(--text-muted)';
        addTerminalLog(`Surveillance System alarm audible state: MUTED.`, 'system');
    } else {
        sirenToggleBtn.innerHTML = `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="btn-icon">
                <path d="M11 5L6 9H2v6h4l5 4V5z"/>
                <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"/>
            </svg>
            MUTE SYSTEM SIREN
        `;
        sirenToggleBtn.style.borderColor = 'var(--neon-red)';
        sirenToggleBtn.style.color = 'var(--neon-red)';
        addTerminalLog(`Surveillance System alarm audible state: ARMED & BROADCASTING.`, 'system');
    }
});

/* ==========================================================================
   5. CONTROLS DECK FEEDBACK (REALTIME RE-STREAM)
   ========================================================================== */

// Config confidence slider behavior
confSlider.addEventListener('input', () => {
    confVal.textContent = parseFloat(confSlider.value).toFixed(2);
});

confSlider.addEventListener('change', () => {
    addTerminalLog(`Confidence threshold updated to: ${confSlider.value}`, 'system');
    reloadStream();
});

// Class Toggles re-stream trigger
classToggles.forEach(toggle => {
    toggle.addEventListener('change', () => {
        const clsName = toggle.nextElementSibling.nextElementSibling.textContent;
        const stateStr = toggle.checked ? 'ENABLED' : 'DISABLED';
        addTerminalLog(`Detection class filter update: ${clsName} ${stateStr}`, 'system');
        reloadStream();
    });
});

function reloadStream() {
    streamLoader.classList.remove('hidden');
    streamPlayer.style.opacity = '0.3';
    streamPlayer.src = getStreamUrl();
}

/* ==========================================================================
   6. CANVAS THREAT TIMELINE CHART (CUSTOM FUTURISTIC CHARTING)
   ========================================================================== */

function renderThreatTimelineChart() {
    const width = threatChart.width;
    const height = threatChart.height;
    
    // Clear canvas
    chartCtx.clearRect(0, 0, width, height);
    
    // Draw Grid Lines
    chartCtx.strokeStyle = 'rgba(255, 59, 59, 0.08)';
    chartCtx.lineWidth = 1;
    
    // Horizontal Grid Lines
    const gridRows = 4;
    for (let r = 0; r <= gridRows; r++) {
        const y = (height / gridRows) * r;
        chartCtx.beginPath();
        chartCtx.moveTo(0, y);
        chartCtx.lineTo(width, y);
        chartCtx.stroke();
    }
    
    // Vertical Grid Lines
    const gridCols = 8;
    for (let c = 0; c <= gridCols; c++) {
        const x = (width / gridCols) * c;
        chartCtx.beginPath();
        chartCtx.moveTo(x, 0);
        chartCtx.lineTo(x, height);
        chartCtx.stroke();
    }
    
    // Set up glow
    chartCtx.shadowBlur = 8;
    chartCtx.shadowColor = 'var(--neon-red)';
    
    // Create fill gradient below threat level
    const gradient = chartCtx.createLinearGradient(0, 0, 0, height);
    gradient.addColorStop(0, 'rgba(255, 59, 59, 0.25)');
    gradient.addColorStop(1, 'rgba(255, 59, 59, 0.0)');
    
    // Draw historical line plot path
    chartCtx.beginPath();
    const xStep = width / (maxHistoryPoints - 1);
    
    threatHistory.forEach((val, index) => {
        // Calculate coords (y-axis inverted in Canvas)
        const x = index * xStep;
        const y = height - (val / 100) * (height - 10) - 5;
        
        if (index === 0) {
            chartCtx.moveTo(x, y);
        } else {
            chartCtx.lineTo(x, y);
        }
    });
    
    // Draw neon boundary stroke
    chartCtx.strokeStyle = 'var(--neon-red)';
    chartCtx.lineWidth = 1.5;
    chartCtx.stroke();
    
    // Close area path for gradient fill
    chartCtx.lineTo((threatHistory.length - 1) * xStep, height);
    chartCtx.lineTo(0, height);
    chartCtx.closePath();
    chartCtx.fillStyle = gradient;
    chartCtx.shadowBlur = 0; // Turn off glow for gradient fill
    chartCtx.fill();
}
