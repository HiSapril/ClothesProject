/**
 * Outfit AI API Client
 * Simplified, lightweight fetch wrapper for frontend developers.
 * Includes automatic JWT token handling and error normalization.
 */

const API_BASE_URL = '/api/v1';

class ApiClient {
    constructor() {
        this.accessToken = localStorage.getItem('access_token');
        this.refreshToken = localStorage.getItem('refresh_token');
    }

    async request(endpoint, options = {}) {
        const url = `${API_BASE_URL}${endpoint}`;

        if (this.accessToken) {
            options.headers = {
                ...options.headers,
                'Authorization': `Bearer ${this.accessToken}`
            };
        }

        try {
            const response = await fetch(url, options);

            if (response.status === 401 && this.refreshToken) {
                const refreshed = await this.refreshTokens();
                if (refreshed) {
                    return this.request(endpoint, options);
                }
            }

            const data = await response.json();

            if (!response.ok) {
                let errorMessage = data.message || 'An unexpected error occurred';
                if (response.status === 429) {
                    errorMessage = `Giới hạn yêu cầu đã vượt mức. Vui lòng thử lại sau ${data.retry_after || 'ít phút'}.`;
                } else if (response.status === 503) {
                    errorMessage = 'Hệ thống đang bảo trì hoặc quá tải. Vui lòng quay lại sau.';
                }

                return {
                    success: false,
                    error_code: data.error_code || `HTTP_${response.status}`,
                    message: errorMessage,
                    request_id: data.request_id
                };
            }

            return { success: true, data };
        } catch (error) {
            return {
                success: false,
                error_code: 'NETWORK_ERROR',
                message: 'Cannot connect to the backend server.'
            };
        }
    }

    async refreshTokens() {
        this.logout();
        return false;
    }

    async login(username, password) {
        const formData = new FormData();
        formData.append('username', username);
        formData.append('password', password);

        const result = await this.request('/auth/login', {
            method: 'POST',
            body: formData
        });

        if (result.success) {
            this.accessToken = result.data.access_token;
            this.refreshToken = result.data.refresh_token;
            localStorage.setItem('access_token', this.accessToken);
            if (this.refreshToken) localStorage.setItem('refresh_token', this.refreshToken);
        }
        return result;
    }

    async register(userData) {
        return this.request('/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(userData)
        });
    }

    logout() {
        this.accessToken = null;
        this.refreshToken = null;
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
    }

    async getEnums() {
        return this.request('/meta/enums');
    }

    async uploadItem(file) {
        const formData = new FormData();
        formData.append('file', file);
        return this.request('/items/upload', {
            method: 'POST',
            body: formData
        });
    }

    async getTaskStatus(taskId) {
        return this.request(`/items/task/${taskId}`);
    }

    async getRecommendations(params) {
        return this.request('/recommend', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params)
        });
    }

    async getMyItems() {
        return this.request('/items/me');
    }

    async updateItem(id, data) {
        return this.request(`/items/${id}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
    }

    async updateProfile(profileData) {
        return this.request('/users/me/profile', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(profileData)
        });
    }

    async deleteItem(itemId) {
        return this.request(`/items/${itemId}`, {
            method: 'DELETE'
        });
    }

    async getWeather(lat, lon) {
        return this.request(`/weather?lat=${lat}&lon=${lon}`);
    }

    async getUpcomingEvents() {
        // Cache-bust: always fetch fresh event list, never use browser cache
        return this.request(`/calendar/events?_t=${Date.now()}`, {
            cache: 'no-store'
        });
    }

    async getDailyEvents(date) {
        return this.request(`/calendar/events/daily?date=${date}`);
    }

    async getMonthlyEvents(year, month) {
        return this.request(`/calendar/events/month?year=${year}&month=${month}`);
    }

    async createEvent(eventData) {
        return this.request('/calendar/events', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(eventData)
        });
    }

    async deleteEvent(eventId) {
        return this.request(`/calendar/events/${eventId}`, {
            method: 'DELETE'
        });
    }

    async updateEvent(eventId, eventData) {
        return this.request(`/calendar/events/${eventId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(eventData)
        });
    }
}

export const api = new ApiClient();
