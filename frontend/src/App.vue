<template>
  <div id="app">
    <!-- 登录加载动画 -->
    <LoadingScreen v-if="showLoading" :pages="loadPages" @complete="onLoadingComplete" />

    <!-- 登录页面 -->
    <LoginPage v-if="!isLoggedIn && !showLoading" @login="onLogin" />

    <!-- 游戏主界面 -->
    <GameMain v-if="isLoggedIn && !showLoading" :token="token" :user="user" @logout="onLogout" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import LoginPage from './components/LoginPage.vue'
import LoadingScreen from './components/LoadingScreen.vue'
import GameMain from './components/GameMain.vue'

const isLoggedIn = ref(false)
const showLoading = ref(false)
const loadPages = ref([])
const token = ref('')
const user = ref({})

function onLogin(data) {
  token.value = data.access_token
  user.value = { account_name: data.account_name, role: data.role }
  loadPages.value = data.load_pages || []
  showLoading.value = true
}

function onLoadingComplete() {
  showLoading.value = false
  isLoggedIn.value = true
}

function onLogout() {
  isLoggedIn.value = false
  token.value = ''
  user.value = {}
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}
body {
  font-family: -apple-system, 'Microsoft YaHei', sans-serif;
  background: #f5f0e6;
  min-height: 100vh;
}
#app {
  min-height: 100vh;
}
</style>