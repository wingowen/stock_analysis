// Stock Analysis Frontend JavaScript

document.addEventListener('DOMContentLoaded', function() {
    const startScanBtn = document.getElementById('startScanBtn');
    const refreshBtn = document.getElementById('refreshBtn');
    const statusText = document.getElementById('statusText');
    const progressFill = document.getElementById('progressFill');
    const signalsBody = document.getElementById('signalsBody');
    const noDataRow = document.getElementById('noDataRow');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const dbTypeValue = document.getElementById('dbTypeValue');
    const dbPathValue = document.getElementById('dbPathValue');

    let statusCheckInterval;

    // Load configuration
    loadConfig();

    // Load initial signals
    loadSignals();

    // Event listeners
    startScanBtn.addEventListener('click', startScan);
    refreshBtn.addEventListener('click', loadSignals);

    function loadConfig() {
        fetch('/api/config')
            .then(response => response.json())
            .then(data => {
                dbTypeValue.textContent = data.use_sqlite ? 'SQLite (本地)' : 'Supabase (云端)';
                dbPathValue.textContent = data.sqlite_path || '-';
            })
            .catch(error => {
                console.error('Error loading config:', error);
                dbTypeValue.textContent = '加载失败';
            });
    }

    function startScan() {
        startScanBtn.disabled = true;
        startScanBtn.textContent = '🔄 扫描中...';

        fetch('/api/scan/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            if (response.ok) {
                // Start polling for status
                startStatusPolling();
            } else {
                throw new Error('扫描启动失败');
            }
        })
        .catch(error => {
            console.error('Error starting scan:', error);
            alert('扫描启动失败，请检查控制台日志');
            resetScanButton();
        });
    }

    function startStatusPolling() {
        statusCheckInterval = setInterval(() => {
            fetch('/api/scan/status')
                .then(response => response.json())
                .then(data => {
                    updateStatusDisplay(data);

                    if (!data.running) {
                        // Scan finished
                        clearInterval(statusCheckInterval);
                        resetScanButton();
                        loadSignals(); // Refresh results
                    }
                })
                .catch(error => {
                    console.error('Error checking status:', error);
                    clearInterval(statusCheckInterval);
                    resetScanButton();
                });
        }, 1000);
    }

    function updateStatusDisplay(status) {
        statusText.textContent = status.message || '扫描中...';
        progressFill.style.width = `${status.progress || 0}%`;
    }

    function resetScanButton() {
        startScanBtn.disabled = false;
        startScanBtn.textContent = '🚀 开始扫描';
    }

    function loadSignals() {
        loadingSpinner.classList.remove('hidden');
        signalsBody.innerHTML = '';

        fetch('/api/signals')
            .then(response => response.json())
            .then(signals => {
                loadingSpinner.classList.add('hidden');

                if (signals.error) {
                    signalsBody.innerHTML = `<tr><td colspan="9" class="no-data">错误: ${signals.error}</td></tr>`;
                    return;
                }

                if (signals.length === 0) {
                    signalsBody.innerHTML = '<tr id="noDataRow"><td colspan="9" class="no-data">暂无数据，请先运行扫描</td></tr>';
                    return;
                }

                signals.forEach(signal => {
                    const row = createSignalRow(signal);
                    signalsBody.appendChild(row);
                });
            })
            .catch(error => {
                loadingSpinner.classList.add('hidden');
                console.error('Error loading signals:', error);
                signalsBody.innerHTML = '<tr><td colspan="9" class="no-data">加载数据失败</td></tr>';
            });
    }

    function createSignalRow(signal) {
        const row = document.createElement('tr');

        const formatNumber = (num, decimals = 4) => {
            return typeof num === 'number' ? num.toFixed(decimals) : num;
        };

        const formatDate = (dateStr) => {
            if (!dateStr) return '-';
            try {
                return new Date(dateStr).toLocaleString('zh-CN');
            } catch {
                return dateStr;
            }
        };

        row.innerHTML = `
            <td>${signal.stock_code || '-'}</td>
            <td>${signal.signal_date || '-'}</td>
            <td>${formatNumber(signal.volume_ratio)}</td>
            <td>${formatNumber(signal.price_change)}</td>
            <td>${signal.max_volume_recent ? signal.max_volume_recent.toLocaleString() : '-'}</td>
            <td>${signal.current_volume ? signal.current_volume.toLocaleString() : '-'}</td>
            <td>${formatNumber(signal.current_price, 2)}</td>
            <td>${signal.source || '-'}</td>
            <td>${formatDate(signal.created_at)}</td>
        `;

        return row;
    }

    // Initial status check
    fetch('/api/scan/status')
        .then(response => response.json())
        .then(data => {
            if (data.running) {
                startScanBtn.disabled = true;
                startScanBtn.textContent = '🔄 扫描中...';
                startStatusPolling();
            }
        })
        .catch(error => console.error('Error checking initial status:', error));
});