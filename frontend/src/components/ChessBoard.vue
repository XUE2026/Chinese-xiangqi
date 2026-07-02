<template>
  <div class="chess-board-wrapper">
    <canvas ref="canvas" :width="canvasWidth" :height="canvasHeight" @click="handleClick"></canvas>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue'

const props = defineProps({
  fen: {
    type: String,
    default: 'rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR',
  },
  mySide: {
    type: String,
    default: null, // 'w' = 红方(下方), 'b' = 黑方(上方)
  },
  isMyTurn: {
    type: Boolean,
    default: false,
  },
  canDrag: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['move'])

const canvas = ref(null)
const canvasWidth = 540
const canvasHeight = 600
const grid = 60 // 每格60px
const offsetX = 30
const offsetY = 30

const selectedPiece = ref(null)
const boardState = ref([])

// 棋子名称映射
const pieceNames = {
  'r': '车', 'n': '马', 'b': '象', 'a': '士', 'k': '将',
  'c': '炮', 'p': '卒',
  'R': '车', 'N': '马', 'B': '相', 'A': '仕', 'K': '帅',
  'C': '炮', 'P': '兵',
}

// 解析FEN
function parseFen(fen) {
  const rows = fen.split('/')
  const board = []
  for (let row = 0; row < 10; row++) {
    const rowData = []
    let col = 0
    const rowStr = rows[row] || '9'
    for (const ch of rowStr) {
      if (ch >= '0' && ch <= '9') {
        const count = parseInt(ch)
        for (let i = 0; i < count; i++) {
          rowData.push(null)
          col++
        }
      } else {
        rowData.push({ type: ch, side: ch === ch.toUpperCase() ? 'w' : 'b' })
        col++
      }
    }
    board.push(rowData)
  }
  return board
}

// 绘制棋盘
function drawBoard(ctx) {
  ctx.fillStyle = '#f4d9a4'
  ctx.fillRect(0, 0, canvasWidth, canvasHeight)

  ctx.strokeStyle = '#8b4513'
  ctx.lineWidth = 1

  // 绘制横线
  for (let i = 0; i < 10; i++) {
    ctx.beginPath()
    ctx.moveTo(offsetX, offsetY + i * grid)
    ctx.lineTo(offsetX + 8 * grid, offsetY + i * grid)
    ctx.stroke()
  }

  // 绘制竖线
  for (let i = 0; i < 9; i++) {
    if (i === 0 || i === 8) {
      ctx.beginPath()
      ctx.moveTo(offsetX + i * grid, offsetY)
      ctx.lineTo(offsetX + i * grid, offsetY + 9 * grid)
      ctx.stroke()
    } else {
      // 上半部分
      ctx.beginPath()
      ctx.moveTo(offsetX + i * grid, offsetY)
      ctx.lineTo(offsetX + i * grid, offsetY + 4 * grid)
      ctx.stroke()
      // 下半部分
      ctx.beginPath()
      ctx.moveTo(offsetX + i * grid, offsetY + 5 * grid)
      ctx.lineTo(offsetX + i * grid, offsetY + 9 * grid)
      ctx.stroke()
    }
  }

  // 绘制九宫格斜线
  ctx.beginPath()
  ctx.moveTo(offsetX + 3 * grid, offsetY)
  ctx.lineTo(offsetX + 5 * grid, offsetY + 2 * grid)
  ctx.moveTo(offsetX + 5 * grid, offsetY)
  ctx.lineTo(offsetX + 3 * grid, offsetY + 2 * grid)
  ctx.stroke()

  ctx.beginPath()
  ctx.moveTo(offsetX + 3 * grid, offsetY + 7 * grid)
  ctx.lineTo(offsetX + 5 * grid, offsetY + 9 * grid)
  ctx.moveTo(offsetX + 5 * grid, offsetY + 7 * grid)
  ctx.lineTo(offsetX + 3 * grid, offsetY + 9 * grid)
  ctx.stroke()

  // 楚河汉界
  ctx.font = '24px serif'
  ctx.fillStyle = '#8b4513'
  ctx.textAlign = 'center'
  ctx.fillText('楚 河', offsetX + 2 * grid, offsetY + 4.5 * grid + 12)
  ctx.fillText('汉 界', offsetX + 6 * grid, offsetY + 4.5 * grid + 12)
}

// 绘制棋子
function drawPiece(ctx, piece, row, col, isSelected) {
  const x = offsetX + col * grid
  const y = offsetY + row * grid

  // 棋子背景
  ctx.beginPath()
  ctx.arc(x, y, 26, 0, Math.PI * 2)

  if (isSelected) {
    ctx.fillStyle = '#ffeb3b'
  } else if (piece.side === 'w') {
    ctx.fillStyle = '#fff5e6'
  } else {
    ctx.fillStyle = '#e6f0fa'
  }
  ctx.fill()

  ctx.strokeStyle = piece.side === 'w' ? '#c41e3a' : '#1a1a1a'
  ctx.lineWidth = 2
  ctx.stroke()

  // 棋子文字
  ctx.font = 'bold 20px serif'
  ctx.fillStyle = piece.side === 'w' ? '#c41e3a' : '#1a1a1a'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.fillText(pieceNames[piece.type] || piece.type, x, y)
}

// 绘制所有棋子
function drawPieces(ctx) {
  for (let row = 0; row < 10; row++) {
    for (let col = 0; col < 9; col++) {
      const piece = boardState.value[row]?.[col]
      if (piece) {
        const isSelected = selectedPiece.value &&
          selectedPiece.value.row === row &&
          selectedPiece.value.col === col
        drawPiece(ctx, piece, row, col, isSelected)
      }
    }
  }
}

// 完整绘制
function draw() {
  if (!canvas.value) return
  const ctx = canvas.value.getContext('2d')
  drawBoard(ctx)
  drawPieces(ctx)
}

// 点击处理
function handleClick(e) {
  if (!props.isMyTurn && !props.canDrag) return

  const rect = canvas.value.getBoundingClientRect()
  const x = e.clientX - rect.left
  const y = e.clientY - rect.top

  const col = Math.round((x - offsetX) / grid)
  const row = Math.round((y - offsetY) / grid)

  if (col < 0 || col > 8 || row < 0 || row > 9) return

  const clickedPiece = boardState.value[row]?.[col]

  if (selectedPiece.value) {
    // 已选中棋子,尝试移动
    if (clickedPiece && clickedPiece.side === selectedPiece.value.piece.side) {
      // 点击自己的棋子,切换选中
      selectedPiece.value = { row, col, piece: clickedPiece }
    } else {
      // 尝试移动到目标位置
      emit('move', {
        from: [selectedPiece.value.row, selectedPiece.value.col],
        to: [row, col],
      })
      selectedPiece.value = null
    }
  } else {
    // 未选中棋子
    if (clickedPiece) {
      // 检查是否是自己的棋子
      if (props.mySide && clickedPiece.side === props.mySide) {
        selectedPiece.value = { row, col, piece: clickedPiece }
      } else if (props.canDrag) {
        // 管理员可以拖拽任意棋子
        selectedPiece.value = { row, col, piece: clickedPiece }
      }
    }
  }

  draw()
}

// 初始化
onMounted(() => {
  boardState.value = parseFen(props.fen)
  nextTick(() => draw())
})

// 监听FEN变化
watch(() => props.fen, (newFen) => {
  boardState.value = parseFen(newFen)
  selectedPiece.value = null
  nextTick(() => draw())
})

// 监听回合变化
watch(() => props.isMyTurn, () => {
  if (!props.isMyTurn) {
    selectedPiece.value = null
  }
  draw()
})
</script>

<style scoped>
.chess-board-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
}

canvas {
  border: 3px solid #8b4513;
  border-radius: 4px;
  cursor: pointer;
}
</style>