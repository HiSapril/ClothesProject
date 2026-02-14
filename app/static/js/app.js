console.log('App version: 1.1.0 (Multiple Outfits Fix)');
const API_BASE = '/api/v1';
let currentToken = localStorage.getItem('token');

// Auth Check
function checkAuth() {
    if (!currentToken && !window.location.pathname.startsWith('/login')) {
        window.location.href = '/login';
        return false;
    }
    return true;
}

async function authFetch(url, options = {}) {
    const headers = {
        ...options.headers,
        'Authorization': `Bearer ${currentToken}`
    };
    const res = await fetch(url, { ...options, headers });
    if (res.status === 401) {
        localStorage.removeItem('token');
        window.location.href = '/login';
    }
    return res;
}

function logout() {
    localStorage.removeItem('token');
    window.location.href = '/login';
}

// State
let items = [];
let currentFilter = 'all';
let userEvents = [];

// DOM Elements
const uploadZone = document.getElementById('uploadZone');
const fileInput = document.getElementById('fileInput');
const galleryGrid = document.getElementById('galleryGrid');
const recommendBtn = document.getElementById('recommendBtn');
const outfitDisplay = document.getElementById('outfitDisplay');
const weatherWidget = document.getElementById('weatherWidget');

// Init
document.addEventListener('DOMContentLoaded', () => {
    if (!checkAuth()) return;
    loadItems();
    loadProfile();
    checkCalendarStatus();
    setupEventListeners();
});

function setupEventListeners() {
    // Upload Handling
    uploadZone.addEventListener('click', () => fileInput.click());

    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.style.borderColor = 'var(--primary-color)';
    });

    uploadZone.addEventListener('dragleave', () => {
        uploadZone.style.borderColor = 'rgba(255, 255, 255, 0.1)';
    });

    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.style.borderColor = 'rgba(255, 255, 255, 0.1)';
        if (e.dataTransfer.files.length) {
            handleBatchUpload(e.dataTransfer.files);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length) {
            handleBatchUpload(e.target.files);
        }
    });

    // Filters
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            currentFilter = e.target.dataset.filter;
            renderGallery();
        });
    });

    // Recommendation
    recommendBtn.addEventListener('click', getRecommendation);

    // Check Weather
    weatherWidget.addEventListener('click', () => {
        checkWeatherOnly();
    });

    // Clear All Items
    const clearAllBtn = document.querySelector('.clear-all-btn');
    if (clearAllBtn) {
        clearAllBtn.addEventListener('click', clearAllItems);
    }
}

function getUserLocation() {
    return new Promise((resolve) => {
        if (!navigator.geolocation) {
            resolve({ lat: 21.0285, lon: 105.8542 }); // Default Hanoi
            return;
        }
        navigator.geolocation.getCurrentPosition(
            (pos) => resolve({ lat: pos.coords.latitude, lon: pos.coords.longitude }),
            () => resolve({ lat: 21.0285, lon: 105.8542 })
        );
    });
}

async function checkWeatherOnly() {
    weatherWidget.innerHTML = '<div style="opacity: 0.8">Đang kiểm tra thời tiết...</div>';

    try {
        const loc = await getUserLocation();
        const res = await authFetch(`${API_BASE}/weather?lat=${loc.lat}&lon=${loc.lon}`);
        const data = await res.json();

        const forecastHtml = (data.forecast || []).map(f => {
            const date = new Date();
            date.setDate(date.getDate() + f.day);
            const dayName = date.toLocaleDateString('vi-VN', { weekday: 'short' });
            return `
                <div class="forecast-chip">
                    <span class="day">${dayName}</span>
                    <ion-icon name="${getWeatherIcon(f.condition)}"></ion-icon>
                    <div class="temp-range">${Math.round(f.max_temp)}° / ${Math.round(f.min_temp)}°</div>
                </div>
            `;
        }).join('');

        const currentCondition = data.condition.trim();
        const descriptionText = data.description.replace('Hiện tại ', '').trim();

        const weatherText = currentCondition.toLowerCase() === descriptionText.toLowerCase()
            ? currentCondition
            : `${currentCondition} • ${descriptionText}`;

        weatherWidget.innerHTML = `
            <h3>${data.location || 'Vị trí hiện tại'}</h3>
            <div style="display: flex; align-items: center; gap: 15px;">
                <ion-icon name="${getWeatherIcon(data.condition)}" style="font-size: 32px; color: #FF9966;"></ion-icon>
                <span style="font-size: 1.5em; font-weight: 700;">${data.temp}°C</span>
            </div>
            <div style="margin-top: 8px; font-size: 0.9em; opacity: 0.7; font-weight: 500;">
                ${weatherText}
            </div>
            <div class="forecast-container">
                ${forecastHtml}
            </div>
        `;
    } catch (err) {
        showToast('Lỗi khi kiểm tra thời tiết', 'error');
        weatherWidget.innerHTML = '<div style="opacity: 0.8">Sẵn sàng kiểm tra thời tiết...</div>';
    }
}

async function handleBatchUpload(files) {
    showToast(`Đang xử lý ${files.length} ảnh...`, 'info');
    for (let i = 0; i < files.length; i++) {
        await handleUpload(files[i]);
    }
    showToast('Hoàn tất tải lên!', 'success');
}

async function handleUpload(file) {
    const formData = new FormData();
    formData.append('file', file);

    try {
        const res = await authFetch(`${API_BASE}/items/upload`, {
            method: 'POST',
            body: formData
        });

        if (!res.ok) throw new Error('Upload failed');

        const data = await res.json();
        items.unshift(data);
        renderGallery();
    } catch (err) {
        showToast(`Lỗi upload ảnh ${file.name}`, 'error');
    }
}

async function loadItems() {
    try {
        const res = await authFetch(`${API_BASE}/items/me`);
        if (res.ok) {
            items = await res.json();
            renderGallery();
        }
    } catch (err) {
        console.error('Lỗi tải tủ đồ:', err);
    }
}

function renderGallery() {
    let filteredItems = items;
    if (currentFilter !== 'all') {
        filteredItems = items.filter(item => {
            if (currentFilter === 'Ao') return item.category_label === 'Áo';
            if (currentFilter === 'Quan') return item.category_label === 'Quần';
            if (currentFilter === 'Vay') return item.category_label === 'Váy';
            if (currentFilter === 'Giay') return item.category_label === 'Giày';
            if (currentFilter === 'AoKhoac') return item.category_label === 'Áo khoác';
            if (currentFilter === 'Dep') return item.category_label === 'Dép';
            if (currentFilter === 'MatKinh') return item.category_label === 'Mắt kính';
            if (currentFilter === 'VongTay') return item.category_label === 'Vòng tay';
            if (currentFilter === 'DongHo') return item.category_label === 'Đồng hồ';
            if (currentFilter === 'DongHo') return item.category_label === 'Đồng hồ';
            return true;
        });
    }

    galleryGrid.innerHTML = filteredItems.map(item => `
        <div class="clothing-item">
            <div class="delete-btn" onclick="deleteItem(event, ${item.id})" title="Xóa món đồ này">
                <ion-icon name="close"></ion-icon>
            </div>
            <img src="${item.processed_image_url || item.image_url}" alt="${item.category_label}">
            <div class="tag">${item.category_label}</div>
        </div>
    `).join('');
}

async function deleteItem(event, id) {
    event.stopPropagation();
    if (!confirm('Bạn có chắc muốn xóa món đồ này khỏi tủ đồ không?')) return;

    try {
        const res = await authFetch(`${API_BASE}/items/${id}`, { method: 'DELETE' });
        if (res.ok) {
            showToast('Đã xóa món đồ');
            await loadItems();
        }
    } catch (err) {
        showToast('Lỗi khi xóa món đồ', 'error');
    }
}

async function clearAllItems() {
    if (!confirm('CẢNH BÁO: Bạn có chắc muốn xóa TOÀN BỘ tủ đồ không? Hành động này không thể hoàn tác.')) return;

    try {
        const res = await authFetch(`${API_BASE}/items/all`, { method: 'DELETE' });
        if (res.ok) {
            const data = await res.json();
            showToast(data.message || 'Đã dọn dẹp tủ đồ cá nhân', 'success');
            await loadItems();
        } else {
            const error = await res.json();
            showToast(`Lỗi: ${error.detail || 'Không thể xóa'}`, 'error');
        }
    } catch (err) {
        console.error('Lỗi khi dọn dẹp tủ đồ:', err);
        showToast('Lỗi kết nối khi dọn dẹp tủ đồ', 'error');
    }
}

// User Profile
async function saveProfile() {
    const payload = {
        gender: document.getElementById('userGender').value,
        age: parseInt(document.getElementById('userAge').value) || null,
        height: parseInt(document.getElementById('userHeight').value) || null,
        weight: parseInt(document.getElementById('userWeight').value) || null
    };

    try {
        const res = await authFetch(`${API_BASE}/users/me/profile`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (res.ok) {
            showToast('Lưu hồ sơ thành công!', 'success');
        } else {
            showToast('Lỗi khi lưu hồ sơ', 'error');
        }
    } catch (err) {
        console.error(err);
        showToast('Lỗi kết nối', 'error');
    }
}

async function loadProfile() {
    try {
        const res = await authFetch(`${API_BASE}/users/me/profile`);
        if (res.ok) {
            const data = await res.json();
            document.getElementById('userGender').value = data.gender || 'Nam';
            document.getElementById('userAge').value = data.age || 20;
            document.getElementById('userHeight').value = data.height || 172;
            document.getElementById('userWeight').value = data.weight || 60;
        } else {
            // Set defaults if user not found (e.g. first run)
            document.getElementById('userGender').value = 'Nam';
            document.getElementById('userAge').value = 20;
            document.getElementById('userHeight').value = 172;
            document.getElementById('userWeight').value = 60;
        }
    } catch (err) {
        console.error('Lỗi tải hồ sơ:', err);
    }
}

function addEvent() {
    const input = document.getElementById('eventInput');
    const text = input.value.trim();
    if (text) {
        userEvents.push(text);
        input.value = '';
        renderEvents();
        // Automatically select the manually entered event
        selectEventForRecommendation(null, text);
    }
}

function removeEvent(index) {
    userEvents.splice(index, 1);
    renderEvents();
}

function renderEvents() {
    const list = document.getElementById('eventList');
    list.innerHTML = userEvents.map((ev, i) => `
        <div class="event-chip">
            <ion-icon name="calendar-outline" style="font-size: 14px;"></ion-icon>
            <span>${ev}</span>
            <span class="remove" onclick="removeEvent(${i})">&times;</span>
        </div>
    `).join('');
}

function getWeatherIcon(condition) {
    const c = condition.toLowerCase();
    if (c.includes('mưa')) return 'rainy';
    if (c.includes('mây')) return 'cloudy';
    if (c.includes('giông')) return 'thunderstorm';
    if (c.includes('tuyết')) return 'snow';
    return 'sunny';
}

async function getRecommendation() {
    recommendBtn.disabled = true;
    recommendBtn.innerHTML = '<div class="loader" style="display:block"></div>';

    const location = await getUserLocation();
    const payload = {
        lat: location.lat,
        lon: location.lon,
        event_titles: userEvents
    };

    if (selectedEventId) {
        payload.selected_event_id = selectedEventId;
    } else if (selectedEventTitle) {
        payload.event_titles = [selectedEventTitle, ...userEvents];
    }

    console.log('Sending recommendation payload:', payload);
    try {
        const res = await authFetch(`${API_BASE}/recommend`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        console.log('Recommendation response status:', res.status);
        const data = await res.json();
        console.log('Recommendation data received:', data);

        weatherWidget.innerHTML = `
            <h3>Thông tin tham khảo</h3>
            <p style="font-size: 1.1em; margin-top: 8px; font-weight: 600;">${data.weather_summary}</p>
            <div style="margin-top: 10px; font-size: 0.9em; opacity: 0.85; padding: 10px; background: rgba(108, 93, 211, 0.1); border-radius: 8px; border: 1px solid rgba(108, 93, 211, 0.2);">
                <ion-icon name="calendar" style="vertical-align: middle; color: var(--primary);"></ion-icon> ${data.occasion_context}
            </div>
        `;

        if (data.outfits && data.outfits.length > 0) {
            renderOutfits(data.outfits);
            showToast(`Đã tạo ${data.outfits.length} gợi ý trang phục!`, 'success');
        } else {
            showToast('Chưa tìm thấy phối đồ phù hợp!', 'info');
            outfitDisplay.innerHTML = '<div style="text-align: center; padding: 20px;">Không tìm thấy trang phục phù hợp với thời tiết này. Hãy thêm nhiều quần áo hơn!</div>';
        }
    } catch (err) {
        showToast('Lỗi khi lấy gợi ý', 'error');
        console.error(err);
    } finally {
        recommendBtn.disabled = false;
        recommendBtn.innerHTML = '<ion-icon name="sparkles-outline" style="font-size: 20px;"></ion-icon><span>Gợi ý trang phục</span>';
    }
}

function renderWeather(data) {
    weatherWidget.innerHTML = `
        <h3>Dự báo thời tiết</h3>
        <p style="font-size: 1.2em; margin-top: 5px">${data.weather_summary}</p>
        <div style="margin-top: 10px; font-size: 0.9em; opacity: 0.8">
            Bối cảnh: ${data.occasion_context}
        </div>
    `;
}

function renderOutfits(outfits) {
    let currentIdx = 0;

    function renderActive() {
        const outfit = outfits[currentIdx];
        const itemsHtml = outfit.items.map(item => `
            <div class="outfit-slot">
                <img src="${item.processed_image_url || item.image_url}" alt="Item">
                <div>
                    <div style="font-weight: 600">${item.category_label}</div>
                    <div style="font-size: 0.85em; color: var(--text-muted)">${item.type}</div>
                </div>
            </div>
        `).join('');

        const paginationHtml = outfits.length > 1 ? `
            <div style="display: flex; justify-content: center; gap: 8px; margin-bottom: 20px;">
                ${outfits.map((_, i) => `
                    <div class="page-dot ${i === currentIdx ? 'active' : ''}" 
                         style="width: 8px; height: 8px; border-radius: 50%; background: ${i === currentIdx ? 'var(--primary)' : 'rgba(255,255,255,0.2)'}; cursor: pointer;"
                         onclick="changeOutfit(${i})"></div>
                `).join('')}
            </div>
        ` : '';

        outfitDisplay.innerHTML = `
            <div style="display: flex; flex-direction: column; gap: 20px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <h4 style="font-size: 14px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 1px;">Gợi ý ${currentIdx + 1}/${outfits.length}</h4>
                    ${outfits.length > 1 ? `
                        <div style="display: flex; gap: 10px;">
                            <button onclick="prevOutfit()" style="background: rgba(255,255,255,0.05); border: 1px solid var(--border); color: white; width: 32px; height: 32px; border-radius: 50%; cursor: pointer;"><ion-icon name="chevron-back"></ion-icon></button>
                            <button onclick="nextOutfit()" style="background: rgba(255,255,255,0.05); border: 1px solid var(--border); color: white; width: 32px; height: 32px; border-radius: 50%; cursor: pointer;"><ion-icon name="chevron-forward"></ion-icon></button>
                        </div>
                    ` : ''}
                </div>

                ${paginationHtml}

                <div style="display: flex; flex-direction: column; gap: 12px;">
                    ${itemsHtml}
                </div>
                
                <div style="background: rgba(108, 93, 211, 0.08); border: 1px solid rgba(108, 93, 211, 0.15); padding: 18px; border-radius: 12px; position: relative; overflow: hidden;">
                    <div style="position: absolute; top: -10px; right: -10px; font-size: 60px; color: var(--primary); opacity: 0.05;">
                        <ion-icon name="color-palette-outline"></ion-icon>
                    </div>
                    
                    <h4 style="font-size: 13px; text-transform: uppercase; color: #8F82FF; margin-bottom: 12px; display: flex; align-items: center; gap: 8px; font-weight: 800; letter-spacing: 0.5px;">
                        <ion-icon name="sparkles" style="color: #FFD700;"></ion-icon> Ghi chú từ Stylist AI
                    </h4>
                    
                    <div style="font-size: 14px; color: var(--text-main); line-height: 1.6; white-space: pre-line;">
                        ${outfit.reason || "Lựa chọn này được tối ưu hóa dựa trên chỉ số cơ thể, thời tiết và bối cảnh sự kiện của bạn."}
                    </div>
                </div>
            </div>
        `;
    }

    // Global helper functions
    window.nextOutfit = () => {
        currentIdx = (currentIdx + 1) % outfits.length;
        renderActive();
    };
    window.prevOutfit = () => {
        currentIdx = (currentIdx - 1 + outfits.length) % outfits.length;
        renderActive();
    };
    window.changeOutfit = (idx) => {
        currentIdx = idx;
        renderActive();
    };

    renderActive();
}

function showToast(msg, type = 'info') {
    const toast = document.createElement('div');
    toast.className = 'toast ' + (type === 'error' ? 'error' : '');
    toast.textContent = msg;
    document.body.appendChild(toast);

    setTimeout(() => toast.classList.add('show'), 10);
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Google Calendar - Premium Upgrade
let calendarCurrentDate = new Date();
let calendarEvents = [];
let selectedEventId = null;
let selectedEventTitle = null;

async function checkCalendarStatus() {
    try {
        const res = await authFetch(`${API_BASE}/calendar/events`);
        const data = await res.json();

        const notConnected = document.getElementById('calNotConnected');
        const connected = document.getElementById('calConnected');

        if (data.connected) {
            notConnected.style.display = 'none';
            connected.style.display = 'block';
            await loadMonthEvents();
        } else {
            notConnected.style.display = 'block';
            connected.style.display = 'none';
        }
    } catch (err) {
        console.error('Lỗi kiểm tra lịch:', err);
    }
}

async function loadMonthEvents() {
    const month = calendarCurrentDate.getMonth() + 1;
    const year = calendarCurrentDate.getFullYear();

    try {
        const res = await authFetch(`${API_BASE}/calendar/events/month?month=${month}&year=${year}`);
        const data = await res.json();

        if (data.connected) {
            calendarEvents = data.events;
            renderCalendar();
        }
    } catch (err) {
        console.error('Lỗi tải sự kiện tháng:', err);
    }
}

function renderCalendar() {
    const monthYear = document.getElementById('calendarMonth');
    const grid = document.getElementById('calendarGrid');

    const year = calendarCurrentDate.getFullYear();
    const month = calendarCurrentDate.getMonth();

    monthYear.textContent = new Intl.DateTimeFormat('vi-VN', { month: 'long', year: 'numeric' }).format(calendarCurrentDate);

    const firstDayOfMonth = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const today = new Date();

    let html = '';

    // Fill empty days from prev month
    for (let i = 0; i < firstDayOfMonth; i++) {
        html += '<div class="calendar-day not-current"></div>';
    }

    for (let day = 1; day <= daysInMonth; day++) {
        const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        const isToday = today.getDate() === day && today.getMonth() === month && today.getFullYear() === year;

        const dayEvents = calendarEvents.filter(ev => {
            const evStart = ev.start.dateTime || ev.start.date;
            return evStart.startsWith(dateStr);
        });

        const hasEventClass = dayEvents.length > 0 ? 'has-event' : '';
        const todayClass = isToday ? 'today' : '';

        html += `
            <div class="calendar-day ${todayClass} ${hasEventClass}" onclick="handleDayClick('${dateStr}', ${JSON.stringify(dayEvents).replace(/"/g, '&quot;')})">
                ${day}
            </div>
        `;
    }

    grid.innerHTML = html;
}

function prevMonth() {
    calendarCurrentDate.setMonth(calendarCurrentDate.getMonth() - 1);
    loadMonthEvents();
}

function nextMonth() {
    calendarCurrentDate.setMonth(calendarCurrentDate.getMonth() + 1);
    loadMonthEvents();
}

function handleDayClick(dateStr, dayEvents) {
    if (dayEvents && dayEvents.length > 0) {
        // Show event selection modal for outfit recommendations
        openEventSelectionModal(dateStr, dayEvents);
    } else {
        // If no events, open to add new for this day
        const start = `${dateStr}T09:00`;
        const end = `${dateStr}T10:00`;
        openEventModal({ start: { dateTime: start }, end: { dateTime: end } });
    }

    // Highlight selected day visually (optional)
    document.querySelectorAll('.calendar-day').forEach(d => d.classList.remove('selected'));
    // Find the clicked element relative to grid... simplified for now.
}

// Modal Management
function openEventModal(event = null) {
    const modal = document.getElementById('eventModal');
    const title = document.getElementById('modalTitle');
    const summary = document.getElementById('eventSummary');
    const startInput = document.getElementById('eventStart');
    const endInput = document.getElementById('eventEnd');
    const deleteBtn = document.getElementById('deleteEventBtn');

    if (event && event.id) {
        selectedEventId = event.id;
        title.textContent = 'Chỉnh sửa sự kiện';
        summary.value = event.summary || '';

        const start = (event.start.dateTime || event.start.date).substring(0, 16);
        const end = (event.end.dateTime || event.end.date).substring(0, 16);
        startInput.value = start;
        endInput.value = end;
        deleteBtn.style.display = 'block';
    } else {
        selectedEventId = null;
        title.textContent = 'Thêm sự kiện';
        summary.value = '';

        if (event && event.start) {
            startInput.value = event.start.dateTime.substring(0, 16);
            endInput.value = event.end.dateTime.substring(0, 16);
        } else {
            const now = new Date();
            const tomorrow = new Date(now);
            tomorrow.setHours(now.getHours() + 1);
            startInput.value = now.toISOString().substring(0, 16);
            endInput.value = tomorrow.toISOString().substring(0, 16);
        }
        deleteBtn.style.display = 'none';
    }

    modal.classList.add('show');
}

function closeEventModal() {
    document.getElementById('eventModal').classList.remove('show');
}

async function saveEvent() {
    const summary = document.getElementById('eventSummary').value;
    const start_time = document.getElementById('eventStart').value;
    const end_time = document.getElementById('eventEnd').value;

    if (!summary) return showToast('Vui lòng nhập tiêu đề', 'error');

    const payload = {
        summary,
        start_time: new Date(start_time).toISOString(),
        end_time: new Date(end_time).toISOString()
    };

    try {
        let res;
        if (selectedEventId) {
            res = await authFetch(`${API_BASE}/calendar/events/${selectedEventId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
        } else {
            res = await authFetch(`${API_BASE}/calendar/events`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
        }

        if (res.ok) {
            showToast(selectedEventId ? 'Đã cập nhật sự kiện' : 'Đã thêm sự kiện mới', 'success');
            closeEventModal();
            loadMonthEvents();
        } else {
            showToast('Lỗi khi lưu sự kiện', 'error');
        }
    } catch (err) {
        showToast('Lỗi kết nối', 'error');
    }
}

async function deleteCurrentEvent() {
    if (!selectedEventId || !confirm('Bạn có chắc muốn xóa sự kiện này không?')) return;

    try {
        const res = await authFetch(`${API_BASE}/calendar/events/${selectedEventId}`, {
            method: 'DELETE'
        });

        if (res.ok) {
            showToast('Đã xóa sự kiện', 'success');
            closeEventModal();
            loadMonthEvents();
        }
    } catch (err) {
        showToast('Lỗi khi xóa sự kiện', 'error');
    }
}

function connectCalendar() {
    window.location.href = `${API_BASE}/calendar/login`;
}

// Event Selection Modal for Recommendations
function openEventSelectionModal(dateStr, dayEvents) {
    const modal = document.getElementById('eventSelectionModal');
    const dateTitle = document.getElementById('eventSelectionDate');
    const eventsList = document.getElementById('eventSelectionList');

    // Format date nicely
    const date = new Date(dateStr);
    const formattedDate = date.toLocaleDateString('vi-VN', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });

    dateTitle.textContent = formattedDate;

    // Render events list
    eventsList.innerHTML = dayEvents.map(event => {
        const startTime = (event.start.dateTime || event.start.date).substring(11, 16);
        const endTime = (event.end.dateTime || event.end.date).substring(11, 16);
        const timeDisplay = startTime && endTime ? `${startTime} - ${endTime}` : 'Cả ngày';

        // Determine occasion badge
        const summary = (event.summary || '').toLowerCase();
        let occasionBadge = 'Thường ngày';
        let occasionColor = '#6C5DD3';

        if (summary.includes('gym') || summary.includes('sport') || summary.includes('tập') || summary.includes('yoga')) {
            occasionBadge = 'Thể thao';
            occasionColor = '#4CAF50';
        } else if (summary.includes('meeting') || summary.includes('họp') || summary.includes('office') || summary.includes('công ty') || summary.includes('phỏng vấn')) {
            occasionBadge = 'Trang trọng';
            occasionColor = '#FF9800';
        } else if (summary.includes('party') || summary.includes('tiệc') || summary.includes('wedding') || summary.includes('đi chơi')) {
            occasionBadge = 'Đi chơi';
            occasionColor = '#E91E63';
        }

        return `
            <div class="event-selection-item">
                <div class="event-selection-main" onclick="selectEventForRecommendation('${event.id}', '${event.summary}')">
                    <div class="event-selection-time">
                        <ion-icon name="time-outline"></ion-icon>
                        ${timeDisplay}
                    </div>
                    <div class="event-selection-title">${event.summary || 'Sự kiện không tên'}</div>
                    <div class="event-selection-occasion" style="background: ${occasionColor}22; color: ${occasionColor}; border: 1px solid ${occasionColor}44;">
                        ${occasionBadge}
                    </div>
                </div>
                <button class="event-selection-edit" onclick="event.stopPropagation(); closeEventSelectionModal(); openEventModal(${JSON.stringify(event).replace(/"/g, '&quot;')});" title="Chỉnh sửa sự kiện">
                    <ion-icon name="create-outline"></ion-icon>
                </button>
            </div>
        `;
    }).join('');

    modal.classList.add('show');
}

function closeEventSelectionModal() {
    document.getElementById('eventSelectionModal').classList.remove('show');
}

async function selectEventForRecommendation(eventId, eventSummary) {
    closeEventSelectionModal(); // Close modal after selection

    if (eventId) {
        selectedEventId = eventId;
        selectedEventTitle = null;
    } else {
        selectedEventId = null;
        selectedEventTitle = eventSummary;
    }

    const contextDiv = document.getElementById('selectedContext');
    const contentDiv = document.getElementById('selectedContextContent');

    contextDiv.style.display = 'block';
    contentDiv.innerHTML = `
        <div style="margin-top: 10px; padding: 12px; background: rgba(108, 93, 211, 0.1); border-radius: 8px; border: 1px solid rgba(108, 93, 211, 0.3);">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                <ion-icon name="calendar" style="color: var(--primary); font-size: 18px;"></ion-icon>
                <span style="font-weight: 600; color: var(--primary);">Sự kiện</span>
            </div>
            <div style="font-size: 14px; opacity: 0.9;">${eventSummary}</div>
        </div>
        <div style="margin-top: 12px; font-size: 13px; opacity: 0.7; text-align: center;">
            Nhấn "Gợi ý trang phục" để xem phối đồ phù hợp
        </div>
    `;

    showToast(`✓ Đã chọn: ${eventSummary}`, 'success');
}

