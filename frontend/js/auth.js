// Auth Manager — Handles JWT Token storage, Login, Register, and Authenticated Requests.

const Auth = {
  TOKEN_KEY: "antigravity_jwt_token",
  USER_KEY: "antigravity_user_data",

  getToken() {
    return localStorage.getItem(this.TOKEN_KEY);
  },

  getUser() {
    const raw = localStorage.getItem(this.USER_KEY);
    return raw ? JSON.parse(raw) : null;
  },

  setAuth(token, user) {
    localStorage.setItem(this.TOKEN_KEY, token);
    localStorage.setItem(this.USER_KEY, JSON.stringify(user));
    this.updateUI();
  },

  clearAuth() {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
    this.updateUI();
  },

  isLoggedIn() {
    return !!this.getToken();
  },

  getAuthHeader() {
    const token = this.getToken();
    return token ? { "Authorization": `Bearer ${token}` } : {};
  },

  updateUI() {
    const user = this.getUser();
    const userBadge = document.getElementById("authUserBadge");
    const loginBtn = document.getElementById("navLoginBtn");
    const logoutBtn = document.getElementById("navLogoutBtn");

    if (user && userBadge) {
      userBadge.textContent = user.full_name || user.email;
      userBadge.classList.remove("d-none");
      if (loginBtn) loginBtn.classList.add("d-none");
      if (logoutBtn) logoutBtn.classList.remove("d-none");
    } else {
      if (userBadge) userBadge.classList.add("d-none");
      if (loginBtn) loginBtn.classList.remove("d-none");
      if (logoutBtn) logoutBtn.classList.add("d-none");
    }
  }
};
