<template>
  <div class="game-container">
    <!-- 左侧面板 -->
    <div class="sidebar">
      <div class="user-info">
        <div class="user-avatar">{{ user.account_name?.charAt(0) || 'U' }}</div>
        <div class="user-details">
          <div class="username">{{ user.account_name }}</div>
          <div class="role">{{ roleLabel }}</div>
        </div>
        <button @click="handleLogout" class="logout-btn">退出</button>
      </div>

      <div class="game-list">
        <h3>游戏房间</h3>
        <div class="room-actions">
          <button @click="showCreateRoom = true" class="create-btn">创建房间</button>
        </div>
        <div class="rooms">
          <div v-for="room in rooms" :key="room.id" class="room-item" @click="joinRoom(room.id)">
            <span class="room-name">{{ room.name }}</span>
            <span class="room-status">{{ room.status }}</span>
          </div>
          <div v-if="rooms.length === 0" class="no-rooms">暂无房间</div>
        </div>
      </div>
    </div>

    <!-- 棋盘区域 -->
    <div class="board-area">
      <div class="game-header">
        <h2>{{ currentRoom?.name || '中国象棋' }}</h2>
        <div class="game-info">
          <span v-if="currentRoom">步时限制: {{ currentRoom.step_time_limit }}分钟</span>
        </div>
      </div>
      <ChessBoard
        ref="boardRef"
        :fen="currentFen"
        :my-side="mySide"
        :is-my-turn="isMyTurn"
        :can-drag="canDrag"
        @move="handleMove"
      />
      <div class="game-controls">
        <button @click="resetBoard" v-if="!currentRoom">重置棋盘</button>
        <button @click="leaveRoom" v-if="currentRoom">离开房间</button>
      </div>
    </div>

    <!-- 右侧面板 -->
    <div class="right-panel">
      <div class="move-history">
        <h3>走棋记录</h3>
        <div class="moves">
          <div v-for="(move, idx) in moveHistory" :key="idx" class="move-item">
            {{ idx + 1 }}. {{ move }}
          </div>
        </div>
      </div>
      <div class="chat-area">
        <h3>聊天</h3>
        <div class="messages">
          <div v-for="(msg, idx) in messages" :key="idx" class="message">
            <span class="msg-user">{{ msg.user }}:</span>
            <span class="msg-text">{{ msg.text }}</span>
          </div>
        </div>
        <div class="chat-input">
          <input v-model="chatText" @keyup.enter="sendChat" placeholder="输入消息..." />
          <button @click="sendChat">发送</button>
        </div>
      </div>
    </div>

    <!-- 创建房间弹窗 -->
    <div v-if="showCreateRoom" class="modal">
      <div class="modal-content">
        <h3>创建游戏房间</h3>
        <div class="form-group">
          <label>房间名称</label>
          <input v-model="newRoom.name" placeholder="输入房间名称" />
        </div>
        <div class="form-group">
          <label>游戏类型</label>
          <select v-model="newRoom.type">
            <option value="normal">标准对局</option>
            <option value="entertain_fun">娱乐棋局</option>
          </select>
        </div>
        <div class="form-group">
          <label>每步时限(分钟)</label>
          <input v-model.number="newRoom.step_time_limit" type="number" min="1" max="30" />
        </div>
        <div class="modal-actions">
          <button @click="createRoom" class="confirm-btn">创建</button>
          <button @click="showCreateRoom = false" class="cancel-btn">取消</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import ChessBoard from './ChessBoard.vue'
import axios from 'axios'
import { io } from 'socket.io-client'

const props = defineProps({
  token: String,
  user: Object,
})

const emit = defineEmits(['logout'])

// 状态
const showCreateRoom = ref(false)
const rooms = ref([])
const currentRoom = ref(null)
const currentFen = ref('rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR')
const mySide = ref(null) // 'w' 红方, 'b' 黑方
const isMyTurn = ref(false)
const canDrag = ref(false) // 管理员拖拽权限
const moveHistory = ref([])
const messages = ref([])
const chatText = ref('')
const boardRef = ref(null)
const socket = ref(null)

const newRoom = ref({
  name: '新棋局',
  type: 'normal',
  step_time_limit: 5,
})

const roleLabel = computed(() => {
  const role = props.user.role
  if (role === 'super_admin') return '超级管理员'
  if (role === 'admin') return '管理员'
  return '棋手'
})

// 初始化Socket.IO
onMounted(() => {
  socket.value = io('http://localhost:8000/game', {
    query: { token: props.token },
    transports: ['websocket'],
  })

  socket.value.on('connect', () => {
    console.log('Socket connected')
  })

  socket.value.on('move_made', (data) => {
    currentFen.value = data.new_fen
    if (data.next_turn === props.user.id) {
      isMyTurn.value = true
    } else {
      isMyTurn.value = false
    }
    // 记录走法
    moveHistory.value.push(`${data.from} -> ${data.to}`)
  })

  socket.value.on('chat', (data) => {
    messages.value.push({ user: data.user, text: data.text })
  })
})

onUnmounted(() => {
  if (socket.value) {
    socket.value.disconnect()
  }
})

// 方法
function handleLogout() {
  axios.post('/auth/logout').finally(() => {
    emit('logout')
  })
}

function resetBoard() {
  currentFen.value = 'rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR'
  moveHistory.value = []
}

async function createRoom() {
  try {
    const res = await axios.post('/admin/games', newRoom.value, {
      headers: { Authorization: `Bearer ${props.token}` },
    })
    if (res.data.status === 'ok') {
      rooms.value.push({
        id: res.data.game_id,
        name: res.data.name,
        status: 'waiting',
        ...newRoom.value,
      })
      showCreateRoom.value = false
    }
  } catch (e) {
    console.error('创建房间失败:', e)
  }
}

async function joinRoom(roomId) {
  if (socket.value) {
    const result = await socket.value.emitWithAck('join_room', { game_id: roomId })
    if (result?.status === 'ok') {
      currentRoom.value = rooms.value.find(r => r.id === roomId)
      // 设置玩家方 (先加入的是红方)
      mySide.value = 'w'
    }
  }
}

function leaveRoom() {
  currentRoom.value = null
  mySide.value = null
  isMyTurn.value = false
  resetBoard()
}

function handleMove(moveData) {
  if (socket.value && currentRoom.value) {
    socket.value.emit('move_piece', {
      game_id: currentRoom.value.id,
      from_pos: moveData.from,
      to_pos: moveData.to,
    })
  }
}

function sendChat() {
  if (socket.value && chatText.value.trim()) {
    socket.value.emit('chat', { text: chatText.value })
    chatText.value = ''
  }
}
</script>

<style scoped>
.game-container {
  display: flex;
  min-height: 100vh;
  padding: 20px;
  gap: 20px;
}

.sidebar {
  width: 250px;
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-bottom: 16px;
  border-bottom: 1px solid #eee;
}

.user-avatar {
  width: 48px;
  height: 48px;
  background: #8b4513;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: bold;
}

.user-details {
  flex: 1;
}

.username {
  font-weight: 600;
  color: #333;
}

.role {
  font-size: 12px;
  color: #666;
}

.logout-btn {
  padding: 6px 12px;
  background: #f5f5f5;
  border: 1px solid #ddd;
  border-radius: 6px;
  cursor: pointer;
}

.game-list {
  margin-top: 20px;
}

.game-list h3 {
  color: #8b4513;
  margin-bottom: 12px;
}

.room-actions {
  margin-bottom: 12px;
}

.create-btn {
  width: 100%;
  padding: 10px;
  background: #8b4513;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.rooms {
  max-height: 300px;
  overflow-y: auto;
}

.room-item {
  padding: 10px;
  background: #f8f4e8;
  border-radius: 6px;
  margin-bottom: 8px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
}

.room-item:hover {
  background: #f0e8d8;
}

.no-rooms {
  color: #999;
  text-align: center;
  padding: 20px;
}

.board-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.game-header {
  text-align: center;
  margin-bottom: 16px;
}

.game-header h2 {
  color: #8b4513;
}

.game-info {
  color: #666;
  font-size: 14px;
}

.game-controls {
  margin-top: 16px;
  display: flex;
  gap: 12px;
}

.game-controls button {
  padding: 10px 20px;
  background: #8b4513;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.right-panel {
  width: 280px;
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.move-history h3,
.chat-area h3 {
  color: #8b4513;
  margin-bottom: 12px;
}

.moves {
  flex: 1;
  max-height: 200px;
  overflow-y: auto;
  background: #f8f4e8;
  border-radius: 6px;
  padding: 10px;
}

.move-item {
  padding: 4px 0;
  font-size: 13px;
}

.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.messages {
  flex: 1;
  max-height: 150px;
  overflow-y: auto;
  background: #f8f4e8;
  border-radius: 6px;
  padding: 10px;
  margin-bottom: 10px;
}

.message {
  margin-bottom: 6px;
  font-size: 13px;
}

.msg-user {
  color: #8b4513;
  font-weight: 500;
}

.msg-text {
  color: #333;
}

.chat-input {
  display: flex;
  gap: 8px;
}

.chat-input input {
  flex: 1;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 6px;
}

.chat-input button {
  padding: 8px 12px;
  background: #8b4513;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-content {
  background: white;
  border-radius: 12px;
  padding: 24px;
  max-width: 400px;
  width: 100%;
}

.modal-content h3 {
  color: #8b4513;
  margin-bottom: 20px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  color: #333;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
}

.modal-actions {
  display: flex;
  gap: 12px;
  margin-top: 20px;
}

.confirm-btn,
.cancel-btn {
  flex: 1;
  padding: 12px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.confirm-btn {
  background: #8b4513;
  color: white;
}

.cancel-btn {
  background: #f5f5f5;
  color: #666;
}
</style>