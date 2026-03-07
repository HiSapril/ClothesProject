import { api } from './api.js';

// --- Simple State ---
let state = {
    items: [],
    selectedStrategy: 'CONTEXT_AWARE',
    selectedOccasion: 'casual',
    selectedEventId: null,
    weather: null,
    pollingInterval: null,
    currentView: 'dashboard',
    currentDate: new Date(),
    events: [],
    editingEventId: null
};

// --- Core Initialization ---
async function init() {
    console.log("🚀 Initializing v1.4.2 Dashboard...");
    try {
        updateStatus();

        console.log("🔍 Checking user session...");
        const userRes = await api.request('/users/me');
        if (userRes.success) {
            console.log("✅ User authenticated:", userRes.data.username);
            document.getElementById('greeting').textContent = `Chào mừng, ${userRes.data.username}!`;
            loadWardrobe();
        } else {
            console.warn("⚠️ Auth failed, redirecting to login");
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            window.location.href = '/login';
            return;
        }

        console.log("🌦️ Fetching weather...");
        updateWeather();

        console.log("📅 Fetching calendar...");
        updateCalendar();

        console.log("🖱️ Setting up listeners...");
        setupListeners();
        console.log("✨ Init complete.");
    } catch (err) {
        console.error("❌ CRITICAL INIT ERROR:", err);
        showToast("Lỗi khởi tạo hệ thống. Vui lòng F5.", "error");
    }
}

async function updateStatus() {
    try {
        const res = await api.request('/admin/version');
        const versionEl = document.getElementById('versionTag');
        const statusTextEl = document.getElementById('statusText');
        const statusDotEl = document.getElementById('statusDot');

        if (res.success) {
            versionEl.textContent = `v${res.data.version || res.data.api_version}`;
            statusTextEl.textContent = "Hệ thống: Sẵn sàng";
            statusDotEl.style.background = "#22c55e";
        } else {
            statusDotEl.style.background = "#ef4444";
            statusTextEl.textContent = "Hệ thống: Ngoại tuyến";
        }
    } catch (e) {
        console.error("Status check failed", e);
    }
}

async function loadWardrobe() {
    const res = await api.getMyItems();
    if (res.success) {
        state.items = res.data;
        renderWardrobe();
        startPollingIfNecessary();
    }
}

function startPollingIfNecessary() {
    const hasProcessing = state.items.some(it =>
        ['QUEUED', 'PROCESSING'].includes(it.status) || it.task_id === 'SYNC_PROCESSED'
    );

    if (hasProcessing && !state.pollingInterval) {
        state.pollingInterval = setInterval(async () => {
            const res = await api.getMyItems();
            if (res.success) {
                const stillProcessing = res.data.some(it => ['QUEUED', 'PROCESSING'].includes(it.status));
                const statusChanged = JSON.stringify(res.data.map(i => i.status)) !== JSON.stringify(state.items.map(i => i.status));

                if (statusChanged) {
                    state.items = res.data;
                    renderWardrobe();
                }

                if (!stillProcessing) {
                    clearInterval(state.pollingInterval);
                    state.pollingInterval = null;
                }
            }
        }, 5000);
    }
}

async function handleUpload(files) {
    if (!files || !files.length) return;
    showToast(`Đang xử lý ${files.length} ảnh...`);

    for (const file of files) {
        try {
            const res = await api.uploadItem(file);
            if (res.success) {
                showToast("Đã thêm vào hàng chờ xử lý!");
                loadWardrobe();
            } else {
                showToast(res.message || "Lỗi tải ảnh", "error");
            }
        } catch (e) {
            console.error("Upload failed", e);
        }
    }
}

async function runRecommendation() {
    const btn = document.getElementById('btnRecommend');
    const originalText = btn.textContent;
    btn.disabled = true;
    btn.textContent = "Đang suy nghĩ...";

    const params = {
        lat: 10.7626,
        lon: 106.6601,
        strategy: state.selectedStrategy,
        force_occasion: state.selectedOccasion,
        selected_event_id: state.selectedEventId
    };

    try {
        const res = await api.getRecommendations(params);
        if (res.success) {
            renderOutfits(res.data.outfits);
        } else {
            showToast(res.message || "Lỗi lấy gợi ý", "error");
        }
    } catch (e) {
        showToast("Lỗi kết nối khi lấy gợi ý", "error");
    } finally {
        btn.disabled = false;
        btn.textContent = originalText;
    }
}

// --- Renderers ---
function renderWardrobe() {
    const grid = document.getElementById('wardrobeGrid');
    if (!grid) return;

    if (state.items.length === 0) {
        grid.innerHTML = '<p class="text-muted" style="grid-column: 1/-1; text-align: center; padding: 40px;">Tủ đồ trống. Hãy thêm đồ mới!</p>';
        return;
    }

    grid.innerHTML = state.items.map(item => {
        const isProcessing = ['QUEUED', 'PROCESSING'].includes(item.status);
        const imgUrl = item.processed_image_url || item.image_url;
        const label = item.category_label || (isProcessing ? 'Đang phân tích...' : 'Đang tải...');

        return `
            <div class="gallery-item ${isProcessing ? 'processing' : ''}" data-id="${item.id}">
                <img src="${imgUrl}" alt="item" class="${item.processed_image_url ? 'bg-removed' : ''}">
                <div class="category-chip">${label}</div>
                <div class="overlay">
                    <ion-icon name="trash" class="clickable" onclick="deleteItem(${item.id})"></ion-icon>
                    <ion-icon name="create-outline" class="clickable" onclick="openEditModal(${item.id}, '${item.category}', '${item.occasion}')"></ion-icon>
                </div>
                ${isProcessing ? '<div class="loader-tiny"></div>' : ''}
            </div>
        `;
    }).join('');
}

function renderBreakdown(breakdown) {
    if (!breakdown || !breakdown.length) return '';

    // Map English labels to Vietnamese and parse values
    const rows = breakdown.map(b => {
        const match = b.match(/([+-]?\d+\.?\d*)$/);
        const val = match ? parseFloat(match[1]) : null;
        const isPositive = val !== null && b.includes('+');
        const isNegative = val !== null && b.includes('-');

        let label = b
            .replace(/:\s*[+-]?\d+\.?\d*$/, '')
            .replace('Base score', 'Điểm nền cơ sở')
            .replace('Full occasion match bonus', 'Khớp bối cảnh hoàn hảo')
            .replace('Occasion match', 'Phù hợp bối cảnh')
            .replace('Occasion mismatch', 'Sai bối cảnh')
            .replace('Cold weather + outerwear', 'Trời lạnh + Áo khoác')
            .replace('Ideal layers for hot weather', 'Trang phục thoáng mát')
            .replace('Cool light colors', 'Màu sáng giải nhiệt')
            .replace('Deep tones for warmth', 'Tông màu ấm áp')
            .replace('AI classification quality', 'Chất lượng AI (Gemini)');

        const colorClass = isPositive ? 'score-pos' : (isNegative ? 'score-neg' : 'score-neu');
        const sign = isPositive ? '+' : '';
        return `<tr><td>${label}</td><td class="${colorClass}">${val !== null ? sign + val : '—'}</td></tr>`;
    });

    return `
        <details class="score-breakdown">
            <summary>📊 Xem cách tính điểm chi tiết</summary>
            <table class="breakdown-table">
                <thead><tr><th>Tiêu chí</th><th>Điểm</th></tr></thead>
                <tbody>${rows.join('')}</tbody>
            </table>
        </details>
    `;
}

function renderOutfits(outfits) {
    const container = document.getElementById('recommendations-container');
    if (!container) return;

    if (!outfits || !outfits.length) {
        container.innerHTML = `
            <div class="empty-state">
                <ion-icon name="alert-circle-outline"></ion-icon>
                <p>Không tìm thấy đủ trang phục để phối bộ. <br>
                <small class="text-muted">Hãy thêm đủ Áo, Quần và Giày vào tủ đồ nhé!</small></p>
            </div>
        `;
        return;
    }

    container.innerHTML = outfits.map((o, idx) => {
        const pct = o.suitability_pct ?? Math.min(100, Math.round(o.score));
        const barColor = pct >= 80 ? '#4ade80' : pct >= 60 ? '#facc15' : '#f87171';
        return `
        <div class="outfit-card ${o.decision_status === 'LOW_CONFIDENCE' ? 'warning-border' : ''}">
            <div class="outfit-header">
                <span class="outfit-rank">#${idx + 1}</span>
                <div class="score-badge" title="Điểm phù hợp trên thang 100">
                    <svg width="42" height="42" viewBox="0 0 42 42">
                        <circle cx="21" cy="21" r="16" fill="none" stroke="#2a2a3a" stroke-width="4"/>
                        <circle cx="21" cy="21" r="16" fill="none" stroke="${barColor}" stroke-width="4"
                            stroke-dasharray="${(pct / 100) * 100.5} 100.5"
                            stroke-dashoffset="25.1"
                            stroke-linecap="round"/>
                    </svg>
                    <span class="score-pct" style="color:${barColor}">${pct}</span>
                    <span class="score-label-100">/100</span>
                </div>
            </div>
            <div class="outfit-images">
                ${o.items.map(it => `
                    <div class="outfit-item-mini">
                        <img src="${it.image_url}" alt="${it.category_label}">
                        <small>${it.category_label}</small>
                    </div>
                `).join('')}
            </div>
            <div class="outfit-footer">
                <p class="explanation-text">
                    <ion-icon name="information-circle-outline"></ion-icon>
                    ${o.reason || 'Sự kết hợp hoàn hảo.'}
                </p>
                ${renderBreakdown(o.breakdown)}
                ${o.decision_status === 'LOW_CONFIDENCE' ? '<p class="text-warning" style="font-size:11px;"><ion-icon name="warning-outline"></ion-icon> AI chưa tin cậy 100%.</p>' : ''}
            </div>
        </div>
    `}).join('');
}

async function updateWeather() {
    try {
        const res = await api.getWeather(10.7626, 106.6601);
        const mini = document.getElementById('weatherMini');
        const info = document.getElementById('weather-info');

        if (res.success && res.data) {
            const content = `
                <div style="text-align: right">
                    <div style="font-weight: 700; font-size: 1.15rem; color: var(--primary);">${res.data.temp}°C</div>
                    <small class="text-muted" style="text-transform: capitalize;">${res.data.condition}</small>
                </div>
            `;
            if (mini) mini.innerHTML = content;
            if (info) info.innerHTML = `Hiện tại: ${res.data.temp}°C, ${res.data.condition}. <br><small>Phù hợp cho các trang phục thoáng mát.</small>`;
        } else {
            if (info) info.innerHTML = '<span class="text-warning">Không lấy được thời tiết.</span>';
        }
    } catch (e) {
        console.warn("Weather UI Error", e);
        const info = document.getElementById('weather-info');
        if (info) info.innerHTML = '<span class="text-danger">Lỗi kết nối thời tiết.</span>';
    }
}

async function updateCalendar() {
    try {
        console.log("fetching upcoming events...");
        const res = await api.getUpcomingEvents();
        const list = document.getElementById('event-list');
        if (!list) return;

        if (res.success) {
            if (res.data.connected === false) {
                list.innerHTML = `
                    <div class="empty-state-mini">
                        <p class="text-muted" style="font-size: 12px; margin-bottom: 8px;">Chưa kết nối Google Calendar.</p>
                        <button onclick="window.location.href='/api/v1/calendar/login'" class="btn-ghost" style="padding: 5px 10px; font-size: 11px;">
                            Kết nối ngay
                        </button>
                    </div>
                `;
                return;
            }

            if (res.data.events && res.data.events.length) {
                list.innerHTML = res.data.events.map(ev => `
                    <div class="event-chip clickable" onclick="selectEvent('${ev.id}', this)">
                        <strong>${ev.title || ev.summary}</strong><br>
                        <small>${ev.date ? ev.date + ' ' : ''}${ev.time || 'Cả ngày'}</small>
                    </div>
                `).join('');
            } else {
                list.innerHTML = '<p class="text-muted">Không có sự kiện hôm nay.</p>';
            }
        } else {
            list.innerHTML = '<p class="text-warning">Lỗi tải sự kiện.</p>';
        }
    } catch (e) {
        console.warn("Calendar UI Error", e);
        const list = document.getElementById('event-list');
        if (list) list.innerHTML = '<p class="text-danger">Mất kết nối Lịch.</p>';
    }
}

// --- Global Functions ---
window.showView = (viewId, event) => {
    state.currentView = viewId;
    document.querySelectorAll('.nav-item').forEach(btn => btn.classList.remove('active'));
    if (event) event.currentTarget.classList.add('active');
    else {
        const target = document.querySelector(`.nav-item[onclick*="${viewId}"]`);
        if (target) target.classList.add('active');
    }

    document.querySelectorAll('.view-content').forEach(el => el.style.display = 'none');

    // Always show wardrobe on dashboard
    const wardrobe = document.querySelector('.wardrobe-panel');
    if (wardrobe) wardrobe.style.display = (viewId === 'dashboard' || viewId === 'wardrobe') ? 'block' : 'none';

    if (viewId === 'dashboard') {
        document.getElementById('view-dashboard').style.display = 'block';
    } else if (viewId === 'calendar') {
        document.getElementById('view-calendar').style.display = 'block';
        renderCalendar();
    } else if (viewId === 'wardrobe') {
        // Wardrobe state handled above
    }
};

window.selectEvent = (id, el) => {
    state.selectedEventId = id;
    document.querySelectorAll('.event-chip').forEach(c => c.classList.remove('active'));
    if (el) el.classList.add('active');

    // Auto-sync occasion active state if possible, but mainly rely on the backend event
    document.querySelectorAll('.occ-btn').forEach(b => b.classList.remove('active'));

    showToast("Đã chọn sự kiện!");
};

window.deleteItem = async (id) => {
    if (confirm("Xóa món đồ này?")) {
        const res = await api.deleteItem(id);
        if (res.success) {
            showToast("Đã xóa.");
            loadWardrobe();
        }
    }
};

window.triggerUpload = () => {
    const input = document.getElementById('fileInput');
    if (input) input.click();
};

window.logout = () => api.logout();

// --- Calendar Logic ---
const monthNames = ["Tháng 1", "Tháng 2", "Tháng 3", "Tháng 4", "Tháng 5", "Tháng 6", "Tháng 7", "Tháng 8", "Tháng 9", "Tháng 10", "Tháng 11", "Tháng 12"];

window.prevMonth = () => {
    state.currentDate.setMonth(state.currentDate.getMonth() - 1);
    renderCalendar();
};

window.nextMonth = () => {
    state.currentDate.setMonth(state.currentDate.getMonth() + 1);
    renderCalendar();
};

let _isRenderingCalendar = false;
async function renderCalendar() {
    if (_isRenderingCalendar) return; // Prevent concurrent renders (causes duplicates)
    _isRenderingCalendar = true;

    const grid = document.getElementById('calendar-grid');
    const title = document.getElementById('currentMonthYear');
    if (!grid) { _isRenderingCalendar = false; return; }

    const year = state.currentDate.getFullYear();
    const month = state.currentDate.getMonth();
    title.textContent = `${monthNames[month]}, ${year}`;

    const firstDay = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();

    // Clear BEFORE any async work to prevent double-render
    grid.innerHTML = '<div style="grid-column:1/-1;text-align:center;padding:20px;color:var(--text-muted)">Đang tải lịch...</div>';

    // Fetch all events for the month once
    const monthRes = await api.getMonthlyEvents(year, month + 1);
    const monthEvents = monthRes.success ? monthRes.data.events : [];

    // Build the full grid in memory first, then inject once
    grid.innerHTML = '';

    // Fill previous days
    const prevDate = new Date(year, month, 0);
    const prevDays = prevDate.getDate();
    for (let i = firstDay - 1; i >= 0; i--) {
        const div = document.createElement('div');
        div.className = 'calendar-day other-month';
        div.innerHTML = `<div class="day-number">${prevDays - i}</div>`;
        grid.appendChild(div);
    }

    // Fill current days
    const today = new Date();
    for (let d = 1; d <= daysInMonth; d++) {
        const div = document.createElement('div');
        div.className = 'calendar-day';
        if (d === today.getDate() && month === today.getMonth() && year === today.getFullYear()) {
            div.classList.add('today');
        }

        const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
        const dayEvents = monthEvents.filter(ev => ev.date === dateStr);

        div.innerHTML = `
            <div class="day-number">${d}</div>
            <div class="day-events" id="day-events-${dateStr}">
                ${dayEvents.map(ev => `<div class="event-dot" title="${ev.summary}">${ev.summary}</div>`).join('')}
            </div>
        `;

        div.onclick = (e) => {
            // Avoid modal if clicking on event dot
            const dateInput = document.getElementById('eventDate');
            if (dateInput) dateInput.value = dateStr;
            openDayModal(dateStr, dayEvents);
        };
        grid.appendChild(div);
    }

    _isRenderingCalendar = false;
}

// --- Modal Handlers ---
window.openDayModal = (dateStr, events) => {
    const modal = document.getElementById('dayEventsModal');
    const title = document.getElementById('dayViewTitle');
    const list = document.getElementById('dayEventsList');
    if (!modal || !list) return;

    // Set state for "Add New" button within this day
    state.selectedDate = dateStr;

    // Format Title: YYYY-MM-DD -> DD/MM/YYYY
    const [y, m, d] = dateStr.split('-');
    title.textContent = `Sự kiện ngày ${d}/${m}/${y}`;

    if (events && events.length) {
        list.innerHTML = events.map(ev => `
            <div class="day-event-item">
                <div class="day-event-info">
                    <h4>${ev.summary}</h4>
                    <p>${ev.time} • ${ev.occasion}</p>
                </div>
                <div class="day-event-actions">
                    <button class="action-btn edit" onclick="editEvent('${ev.id}')" title="Sửa">
                        <ion-icon name="create-outline"></ion-icon>
                    </button>
                    <button class="action-btn delete" onclick="deleteCalendarEvent('${ev.id}')" title="Xóa">
                        <ion-icon name="trash-outline"></ion-icon>
                    </button>
                </div>
            </div>
        `).join('');
    } else {
        list.innerHTML = '<div class="empty-state-mini"><p class="text-muted">Không có sự kiện nào.</p></div>';
    }

    modal.style.display = 'block';
};

window.closeDayModal = () => document.getElementById('dayEventsModal').style.display = 'none';

window.openEventFromDay = () => {
    state.editingEventId = null;
    document.getElementById('eventModalTitle').textContent = "Thêm sự kiện mới";
    document.getElementById('btnSaveEvent').textContent = "Lưu sự kiện";
    document.getElementById('eventForm').reset();

    // Auto-fill the date from the day we clicked
    if (state.selectedDate) {
        document.getElementById('eventDate').value = state.selectedDate;
    }

    closeDayModal();
    openEventModal();
};

window.editEvent = async (id) => {
    showToast("Đang tải dữ liệu...");
    // Ideally we already have the event details in monthEvents, but let's be safe
    // For now, let's find it in our current month view or fetch if needed.
    // Simplifying: we'll fetch to ensure fresh data
    try {
        const res = await api.request(`/calendar/events/${id}`);
        if (res.success) {
            const ev = res.data;
            state.editingEventId = id;
            document.getElementById('eventModalTitle').textContent = "Chỉnh sửa sự kiện";
            document.getElementById('btnSaveEvent').textContent = "Cập nhật sự kiện";

            document.getElementById('eventSummary').value = ev.summary;
            document.getElementById('eventDescription').value = ev.description || "";

            // ISO 8601: 2026-03-07T10:00:00Z
            const start = ev.start_time || "";
            if (start.includes('T')) {
                const [date, time] = start.split('T');
                document.getElementById('eventDate').value = date;
                document.getElementById('eventTime').value = time.substring(0, 5);
            }

            closeDayModal();
            openEventModal();
        }
    } catch (e) {
        showToast("Lỗi tải sự kiện", "error");
    }
};

window.deleteCalendarEvent = async (id) => {
    if (!confirm("Bạn có chắc chắn muốn xóa sự kiện này?")) return;

    const res = await api.deleteEvent(id);
    if (res.success) {
        showToast("Đã xóa sự kiện!");
        closeDayModal();
        _isRenderingCalendar = false;
        await renderCalendar();
        await updateCalendar();
    } else {
        showToast(res.message || "Không thể xóa", "error");
    }
};

window.openEventModal = () => {
    if (!state.editingEventId) {
        document.getElementById('eventModalTitle').textContent = "Thêm sự kiện mới";
        document.getElementById('btnSaveEvent').textContent = "Lưu sự kiện";
    }
    document.getElementById('eventModal').style.display = 'block';
};
window.closeEventModal = () => document.getElementById('eventModal').style.display = 'none';
window.openEditModal = (id, cat, occ) => {
    const idField = document.getElementById('editItemId');
    if (idField) idField.value = id;
    const catField = document.getElementById('editCategory');
    if (catField) catField.value = cat;
    const occField = document.getElementById('editOccasion');
    if (occField) occField.value = occ;
    document.getElementById('editItemModal').style.display = 'block';
};
window.closeEditModal = () => document.getElementById('editItemModal').style.display = 'none';

function setupListeners() {
    const fileInput = document.getElementById('fileInput');
    if (fileInput) fileInput.onchange = (e) => handleUpload(e.target.files);

    const btnRec = document.getElementById('btnRecommend');
    if (btnRec) btnRec.onclick = runRecommendation;

    const eventForm = document.getElementById('eventForm');
    if (eventForm) {
        eventForm.onsubmit = async (e) => {
            e.preventDefault();
            const dateStr = document.getElementById('eventDate').value;
            const timeStr = document.getElementById('eventTime').value;
            const isoTime = new Date(`${dateStr}T${timeStr}:00`).toISOString();

            const data = {
                summary: document.getElementById('eventSummary').value,
                description: document.getElementById('eventDescription').value,
                start_time: isoTime,
                end_time: isoTime
            };

            let res;
            if (state.editingEventId) {
                res = await api.updateEvent(state.editingEventId, data);
            } else {
                res = await api.createEvent(data);
            }

            if (res.success) {
                showToast(state.editingEventId ? "Đã cập nhật sự kiện!" : "Đã thêm sự kiện!");
                state.editingEventId = null;
                closeEventModal();
                // Reset guard so calendar always re-renders fresh
                _isRenderingCalendar = false;
                await renderCalendar();
                await updateCalendar(); // Refresh the event context chips on dashboard
            } else {
                showToast(res.message || 'Không thể lưu sự kiện.', 'error');
            }
        };
    }

    const editForm = document.getElementById('editItemForm');
    if (editForm) {
        editForm.onsubmit = async (e) => {
            e.preventDefault();
            const id = document.getElementById('editItemId').value;
            const data = {
                category: document.getElementById('editCategory').value,
                occasion: document.getElementById('editOccasion').value
            };
            const res = await api.updateItem(id, data);
            if (res.success) {
                showToast("Đã cập nhật!");
                closeEditModal();
                loadWardrobe();
            }
        };
    }

    document.querySelectorAll('.strat-btn').forEach(btn => {
        btn.onclick = () => {
            document.querySelectorAll('.strat-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            state.selectedStrategy = btn.dataset.val;
        };
    });

    document.querySelectorAll('.occ-btn').forEach(btn => {
        btn.onclick = () => {
            document.querySelectorAll('.occ-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            state.selectedOccasion = btn.dataset.val;
            // Clear calendar event selection when manually picking an occasion
            if (state.selectedEventId) {
                state.selectedEventId = null;
                document.querySelectorAll('.event-chip').forEach(c => c.classList.remove('active'));
                showToast("Đã ưu tiên bối cảnh thủ công.");
            }
        };
    });
}

function showToast(msg, type = 'info') {
    const t = document.getElementById('toast');
    if (!t) return;
    t.textContent = msg;
    t.style.borderLeft = `5px solid ${type === 'error' ? '#ef4444' : '#6366f1'}`;
    t.classList.add('show');
    setTimeout(() => t.classList.remove('show'), 3000);
}

// Bootstrap
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
