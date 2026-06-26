document.getElementById('csvFile').setAttribute('accept', '.csv,.json,.xlsx,.xls');

const scriptInput = document.getElementById('dslScript');
const downloadLink = document.getElementById('downloadLink');
const outputDiv = document.getElementById('output');
const previewContainer = document.getElementById('previewContainer');
const previewTable = document.getElementById('previewTable');

let currentFilePreviewData = [];
let processedPreviewData = [];
let showingProcessed = false;

function formatResult(result) {
    if (!result) {
        return '';
    }
    if (result.type === 'table') {
        return 'Command result is available in the preview pane.';
    }
    if (result.type === 'value') {
        if (typeof result.value === 'string') {
            return result.value;
        }
        return JSON.stringify(result.value, null, 2);
    }
    return '';
}

function renderTable(data, container) {
    if (!data || !Array.isArray(data) || data.length === 0) {
        container.innerHTML = '<div style="color:#888;font-size:1em;">No data to display.</div>';
        return;
    }
    let html = '<table><thead><tr>';
    Object.keys(data[0]).forEach(col => {
        html += `<th>${col}</th>`;
    });
    html += '</tr></thead><tbody>';
    data.slice(0, 50).forEach(row => {
        html += '<tr>';
        Object.values(row).forEach(val => {
            html += `<td>${val === null ? '' : val}</td>`;
        });
        html += '</tr>';
    });
    html += '</tbody></table>';
    container.innerHTML = html;
}

function updatePreview() {
    const previewTitle = document.getElementById('previewTitle');
    const previewTable = document.getElementById('previewTable');
    if (showingProcessed) {
        previewTitle.textContent = 'Processed Preview';
        renderTable(processedPreviewData, previewTable);
    } else {
        previewTitle.textContent = 'Current File Preview';
        renderTable(currentFilePreviewData, previewTable);
    }
}

// Show current file preview when file is uploaded
document.getElementById('csvFile').addEventListener('change', function(e) {
    const file = e.target.files[0];
    currentFilePreviewData = [];
    if (!file) {
        updatePreview();
        return;
    }
    const ext = file.name.split('.').pop().toLowerCase();
    if (['csv', 'txt'].includes(ext)) {
        const reader = new FileReader();
        reader.onload = function(evt) {
            const text = evt.target.result;
            const rows = text.split(/\r?\n/).filter(Boolean);
            if (rows.length === 0) {
                currentFilePreviewData = [];
                updatePreview();
                return;
            }
            const headers = rows[0].split(',');
            const data = rows.slice(1).map(row => {
                const values = row.split(',');
                const obj = {};
                headers.forEach((h, i) => obj[h.trim()] = values[i] !== undefined ? values[i].trim() : '');
                return obj;
            });
            currentFilePreviewData = data;
            showingProcessed = false;
            updatePreview();
        };
        reader.readAsText(file);
    } else if (['json'].includes(ext)) {
        const reader = new FileReader();
        reader.onload = function(evt) {
            try {
                const json = JSON.parse(evt.target.result);
                let data = Array.isArray(json) ? json : (json.data || []);
                if (!Array.isArray(data)) data = [data];
                currentFilePreviewData = data;
            } catch {
                currentFilePreviewData = [];
            }
            showingProcessed = false;
            updatePreview();
        };
        reader.readAsText(file);
    } else {
        currentFilePreviewData = [];
        showingProcessed = false;
        updatePreview();
    }
});

document.getElementById('togglePreviewBtn').addEventListener('click', function() {
    showingProcessed = !showingProcessed;
    updatePreview();
    this.textContent = showingProcessed ? 'Show Current File Preview' : 'Show Processed Preview';
});

function renderPreviewTable(data) {
    processedPreviewData = data || [];
    showingProcessed = true;
    updatePreview();
    document.getElementById('togglePreviewBtn').textContent = 'Show Current File Preview';
}

document.getElementById('runButton').addEventListener('click', async function() {
    const fileInput = document.getElementById('csvFile');
    let errorDiv = document.getElementById('error-message');
    if (!errorDiv) {
        errorDiv = document.createElement('div');
        errorDiv.id = 'error-message';
        errorDiv.style.color = 'red';
        errorDiv.style.marginTop = '10px';
        scriptInput.parentNode.insertBefore(errorDiv, downloadLink);
    }

    errorDiv.style.display = 'none';
    outputDiv.textContent = '';

    if (!fileInput.files.length) {
        errorDiv.textContent = 'Please select a CSV or JSON file.';
        errorDiv.style.display = 'block';
        return;
    }
    if (!scriptInput.value.trim()) {
        errorDiv.textContent = 'Please enter a DSL script.';
        errorDiv.style.display = 'block';
        return;
    }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('script', scriptInput.value);

    try {
        const response = await fetch('/run-script', {
            method: 'POST',
            body: formData
        });
        const text = await response.text();
        let result;
        try {
            result = JSON.parse(text);
        } catch (jsonErr) {
            try {
                const safeText = text
                    .replace(/\bNaN\b/g, 'null')
                    .replace(/\bInfinity\b/g, 'null')
                    .replace(/\b-Infinity\b/g, 'null');
                result = JSON.parse(safeText);
            } catch (parseErr) {
                errorDiv.textContent = 'Server returned invalid JSON (possible NaN/Infinity in data).';
                errorDiv.style.display = 'block';
                return;
            }
        }
        if (result.filename) {
            downloadLink.href = `/download/${result.filename}`;
            downloadLink.style.display = 'inline';
            errorDiv.style.display = 'none';
        } else {
            downloadLink.removeAttribute('href');
            downloadLink.style.display = 'none';
        }

        if (result.error) {
            errorDiv.textContent = result.error || 'Processing failed.';
            errorDiv.style.display = 'block';
            outputDiv.textContent = '';
            processedPreviewData = [];
            showingProcessed = false;
            updatePreview();
            return;
        }

        const resultMessage = formatResult(result.result);
        outputDiv.textContent = resultMessage ? `${result.message || 'Processing complete'}\n${resultMessage}` : (result.message || 'Processing complete');

        if (result.result && result.result.type === 'table' && result.result.preview) {
            renderPreviewTable(result.result.preview);
        } else if (result.preview) {
            renderPreviewTable(result.preview);
        } else {
            processedPreviewData = [];
            showingProcessed = false;
            updatePreview();
        }
    } catch (err) {
        errorDiv.textContent = 'Network or server error.';
        errorDiv.style.display = 'block';
        outputDiv.textContent = '';
        console.error('Run Script Error:', err);
    }
});

document.getElementById('clearButton').addEventListener('click', function() {
    document.getElementById('csvFile').value = '';
    scriptInput.value = '';
    downloadLink.style.display = 'none';
    outputDiv.textContent = '';
    processedPreviewData = [];
    currentFilePreviewData = [];
    showingProcessed = false;
    updatePreview();
    localStorage.removeItem('dslScript');
});

document.getElementById('sampleButton').addEventListener('click', function() {
    scriptInput.value = "DROP 'b';\nRENAME 'a' TO 'alpha';\nSAVE 'out.csv';";
    outputDiv.textContent = 'Sample DSL script loaded. Please upload a sample CSV.';
    localStorage.setItem('dslScript', scriptInput.value);
});

document.getElementById('dslRefButton').addEventListener('click', function() {
    document.getElementById('dslRefModal').style.display = 'flex';
});
document.getElementById('closeDslRef').addEventListener('click', function() {
    document.getElementById('dslRefModal').style.display = 'none';
});

document.getElementById('downloadLogButton').addEventListener('click', function() {
    fetch('/download/app.log').then(resp => {
        if (resp.ok) return resp.blob();
        else throw new Error('Log not found');
    }).then(blob => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'app.log';
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
    }).catch(() => {
        outputDiv.textContent = 'Log file not found.';
    });
});

scriptInput.addEventListener('input', function() {
    localStorage.setItem('dslScript', scriptInput.value);
});
window.addEventListener('DOMContentLoaded', function() {
    const saved = localStorage.getItem('dslScript');
    if (saved) scriptInput.value = saved;
    updatePreview();
});
