<template>
  <div class="login-container">
    <div class="login-card">
      <h1>中国象棋对战平台</h1>
      <p class="subtitle">楚河汉界，运筹帷幄</p>

      <div class="form-group">
        <label>账号</label>
        <input v-model="account" type="text" placeholder="请输入账号" />
      </div>

      <div class="form-group">
        <label>密码</label>
        <input v-model="password" type="password" placeholder="请输入密码" />
      </div>

      <div class="form-group">
        <label>OTP验证码 (临时用户必填)</label>
        <input v-model="otp" type="text" placeholder="6位数字验证码" maxlength="6" />
      </div>

      <button @click="handleLogin" :disabled="loading">
        {{ loading ? '登录中...' : '登录' }}
      </button>

      <div v-if="error" class="error-msg">{{ error }}</div>

      <div class="demo-info">
        <p>测试账号:</p>
        <p>管理员: admin / admin123456</p>
        <p>普通用户: testuser / testpass123</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'

const emit = defineEmits(['login'])

const account = ref('')
const password = ref('')
const otp = ref('')
const loading = ref(false)
const error = ref('')

async function handleLogin() {
  if (!account.value || !password.value) {
    error.value = '请输入账号和密码'
    return
  }

  loading.value = true
  error.value = ''

  try {
    const res = await axios.post('/auth/login', {
      account_name: account.value,
      password: password.value,
      otp_code: otp.value || undefined,
    })

    if (res.data.status === 'ok') {
      emit('login', {
        access_token: res.data.access_token,
        account_name: account.value,
        role: 'player',
        load_pages: res.data.load_pages,
      })
    } else {
      error.value = res.data.detail || '登录失败'
    }
  } catch (e) {
    error.value = e.response?.data?.detail || '网络错误'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.login-card {
  background: white;
  border-radius: 12px;
  padding: 32px;
  max-width: 400px;
  width: 100%;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

h1 {
  color: #8b4513;
  text-align: center;
  margin-bottom: 8px;
}

.subtitle {
  color: #666;
  text-align: center;
  margin-bottom: 24px;
  font-size: 14px;
}

.form-group {
  margin-bottom: 16px;
}

label {
  display: block;
  margin-bottom: 6px;
  color: #333;
  font-weight: 500;
}

input {
  width: 100%;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  transition: border-color 0.2s;
}

input:focus {
  outline: none;
  border-color: #8b4513;
}

button {
  width: 100%;
  padding: 14px;
  background: #8b4513;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  cursor: pointer;
  transition: background 0.2s;
}

button:hover:not(:disabled) {
  background: #6b3410;
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error-msg {
  color: #c41e3a;
  background: #fee;
  padding: 10px;
  border-radius: 6px;
  margin-top: 12px;
  text-align: center;
}

.demo-info {
  margin-top: 20px;
  padding: 12px;
  background: #f8f4e8;
  border-radius: 6px;
  font-size: 12px;
  color: #666;
}

.demo-info p {
  margin: 4px 0;
}
</style>