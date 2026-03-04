import { api } from './api.js';

// --- State Management ---
let state = {
    user: null,
    items: [],
    enums: null,
    isUploading: false,
    activeTasks: new Set()
};

// --- Initialization ---
document.addEventListener('DOMContentLoaded', async () => {
    // 0. Fetch Public Config
    const configRes = await api.request('/meta/config');
    if (configRes.success) {
        if (configRes.data.demo_mode) {
            document.getElementById('demoBanner').style.display = 'flex';
        }
        console.log("Config loaded:", configRes.data);
    }

    // 1. Initial Meta Fetch
    const enumRes = await api.getEnums();
    if (enumRes.success) {
        state.enums = enumRes.data;
        console.log("Metadata loaded:", state.enums);
    }

    // 2. Auth Check
    const userRes = await api.request('/users/me');
    if (userRes.success) {
        state.user = userRes.data;
        updateUI();
        loadWardrobe();
    } else {
        // Redirect to login if on protected page
        if (!window.location.pathname.includes('login')) {
            window.location.href = '/login';
        }
    }

    // 3. Operational Check
    checkOperationalStatus();
    setInterval(checkOperationalStatus, 10000); // Check every 10s

    // 4. Event Listeners
    setupEventListeners();
});

function setupEventListeners() {
    const uploadZone = document.getElementById('uploadZone');
    const fileInput = document.getElementById('fileInput');

    uploadZone.onclick = () => fileInput.click();
    fileInput.onchange = (e) => handleFileUpload(e.target.files);

    document.getElementById('recommendBtn').onclick = requestRecommendations;
}

// --- Wardrobe Actions ---
async function loadWardrobe() {
    const res = await api.getMyItems();
    if (res.success) {
        state.items = res.data;
        renderGallery();
    }
}

async function handleFileUpload(files) {
    if (!files.length) return;

    showToast(`Đang tải lên ${files.length} ảnh...`);

    for (const file of files) {
        const res = await api.uploadItem(file);
        if (res.success) {
            const { item_id, task_id } = res.data;
            if (task_id !== "ALREADY_PROCESSED") {
                pollTask(task_id, item_id);
            } else {
                showToast("Ảnh này đã tồn tại trong tủ đồ.");
                loadWardrobe();
            }
        } else {
            showToast(`Lỗi: ${res.message}`, "error");
        }
    }
}

// --- Polling Logic ---
async function pollTask(taskId, itemId) {
    if (state.activeTasks.has(taskId)) return;
    state.activeTasks.add(taskId);

    const interval = setInterval(async () => {
        const res = await api.getTaskStatus(taskId);
        if (res.success) {
            const { status, failure_reason } = res.data;

            if (status === 'SUCCESS' || status === 'FAILURE') {
                clearInterval(interval);
                state.activeTasks.delete(taskId);

                if (status === 'SUCCESS') {
                    showToast("Xử lý ảnh hoàn tất!");
                    loadWardrobe();
                } else {
                    showToast(`Xử lý thất bại: ${failure_reason || 'Lỗi không xác định'}`, "error");
                }
            }
        } else {
            // Probably network error, don't stop yet
            console.warn("Poll failed, retrying...");
        }
    }, 2000);
}

// --- Recommendation Logic ---
async function requestRecommendations() {
    const btn = document.getElementById('recommendBtn');
    btn.disabled = true;
    btn.innerHTML = '<ion-icon name="sync-outline" class="spin"></ion-icon> Đang suy nghĩ...';

    // Mock location for demo
    const params = {
        lat: 10.7626,
        lon: 106.6601,
        force_occasion: "casual"
    };

    const res = await api.getRecommendations(params);
    btn.disabled = false;
    btn.innerHTML = '<ion-icon name="sparkles-outline"></ion-icon> <span>Gợi ý trang phục</span>';

    if (res.success) {
        renderOutfits(res.data.outfits);
        showToast("Đã tìm thấy các bộ phối phù hợp!");
    } else {
        showToast(res.message, "error");
    }
}

// --- Rendering Logic ---
function renderGallery() {
    const grid = document.getElementById('galleryGrid');
    grid.innerHTML = state.items.map(item => `
        <div class="gallery-item" data-id="${item.id}">
            <img src="${item.image_url}" alt="Clothing">
            <div class="item-overlay">
                <span class="badge ${item.status.toLowerCase()}">${item.status}</span>
                ${item.category_label ? `<p>${item.category_label}</p>` : ''}
            </div>
        </div>
    `).join('');
}

function renderOutfits(outfits) {
    const display = document.getElementById('outfitDisplay');
    if (!outfits.length) {
        display.innerHTML = '<p class="text-muted">Không tìm thấy bộ phối phù hợp. Thêm nhiều đồ hơn nhé!</p>';
        return;
    }

    display.innerHTML = outfits.map((outfit, index) => `
        <div class="outfit-card">
            <div class="outfit-header">Phối đồ #${index + 1} (Điểm: ${outfit.score})</div>
            <div class="outfit-images">
                ${outfit.items.map(it => `<img src="${it.image_url}" title="${it.category_label}">`).join('')}
            </div>
            <p class="outfit-reason">${outfit.reason || 'Sự lựa chọn hoàn hảo cho ngày hôm nay.'}</p>
        </div>
    `).join('');
}

// --- UI Utilities ---
function showToast(message, type = "info") {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast show ${type}`;
    setTimeout(() => { toast.className = "toast"; }, 3000);
}

function updateUI() {
    if (state.user) {
        document.querySelector('.avatar').textContent = state.user.username[0].toUpperCase();
    }
}

window.logout = () => api.logout();

// --- Operational Checks ---
async function checkOperationalStatus() {
    const res = await api.request('/admin/readiness');
    const readyEl = document.getElementById('sysReady');
    const versionEl = document.getElementById('sysVersion');

    if (res.success) {
        const { status } = res.data;
        readyEl.textContent = status === "READY" ? "● Hệ thống: Sẵn sàng" : "● Hệ thống: Suy giảm";
        readyEl.style.color = status === "READY" ? "#4dff88" : "#ffb347";

        // Fetch version info
        const verRes = await api.request('/admin/version');
        if (verRes.success) {
            versionEl.textContent = `v${verRes.data.api_version}`;
        }
    } else {
        readyEl.textContent = "● Hệ thống: Ngoại tuyến";
        readyEl.style.color = "#ff4d4d";
    }
}
