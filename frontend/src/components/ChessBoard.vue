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
    default: null,
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
const grid = 60
const offsetX = 30
const offsetY = 30

const selectedPiece = ref(null)
const boardState = ref([])

const pieceNames = {
  'r': '车', 'n': '马', 'b': '象', 'a': '士', 'k': '将',
  'c': '炮', 'p': '卒',
  'R': '车', 'N': '马', 'B': '相', 'A': '仕', 'K': '帅',
  'C': '炮', 'P': '兵',
}

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

function drawBoard(ctx) {
  ctx.fillStyle = '#f4d9a4'
  ctx.fillRect(0, 0, canvasWidth, canvasHeight)

  ctx.strokeStyle = '#8b4513'
  ctx.lineWidth = 1

  for (let i = 0; i < 10; i++) {
    ctx.beginPath()
    ctx.moveTo(offsetX, offsetY + i * grid)
    ctx.lineTo(offsetX + 8 * grid, offsetY + i * grid)
    ctx.stroke()
  }

  for (let i = 0; i < 9; i++) {
    if (i === 0 || i === 8) {
      ctx.beginPath()
      ctx.moveTo(offsetX + i * grid, offsetY)
      ctx.lineTo(offsetX + i * grid, offsetY + 9 * grid)
      ctx.stroke()
    } else {
      ctx.beginPath()
      ctx.moveTo(offsetX + i * grid, offsetY)
      ctx.lineTo(offsetX + i * grid, offsetY + 4 * grid)
      ctx.stroke()
      ctx.beginPath()
      ctx.moveTo(offsetX + i * grid, offsetY + 5 * grid)
      ctx.lineTo(offsetX + i * grid, offsetY + 9 * grid)
      ctx.stroke()
    }
  }

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

  ctx.font = '24px serif'
  ctx.fillStyle = '#8b4513'
  ctx.textAlign = 'center'
  ctx.fillText('楚 河', offsetX + 2 * grid, offsetY + 4.5 * grid + 12)
  ctx.fillText('汉 界', offsetX + 6 * grid, offsetY + 4.5 * grid + 12)
}

function drawPiece(ctx, piece, row, col, isSelected) {
  const x = offsetX + col * grid
  const y = offsetY + row * grid
  const radius = 26
  const liftY = isSelected ? -8 : 0

  if (isSelected) {
    ctx.beginPath()
    ctx.arc(x, y + 8, radius - 2, 0, Math.PI * 2)
    ctx.fillStyle = 'rgba(0,0,0,0.3)'
    ctx.fill()
  }

  const isRed = piece.side === 'w'
  const baseColor = isRed ? '#c41e3a' : '#1a1a1a'
  const bgLight = isRed ? '#fff5e6' : '#e6f0fa'
  const bgDark = isRed ? '#ffe4c4' : '#d4e0f0'

  ctx.beginPath()
  ctx.ellipse(x, y + liftY, radius, radius - 3, 0, 0, Math.PI * 2)

  const gradient = ctx.createRadialGradient(x - 6, y + liftY - 6, 0, x, y + liftY, radius)
  if (isRed) {
    gradient.addColorStop(0, '#fffcf7')
    gradient.addColorStop(0.3, '#fff5e6')
    gradient.addColorStop(0.7, '#ffe4c4')
    gradient.addColorStop(1, '#f5d0a0')
  } else {
    gradient.addColorStop(0, '#f8fafc')
    gradient.addColorStop(0.3, '#e6f0fa')
    gradient.addColorStop(0.7, '#d4e0f0')
    gradient.addColorStop(1, '#b8c8d8')
  }
  ctx.fillStyle = gradient
  ctx.fill()

  ctx.beginPath()
  ctx.ellipse(x, y + liftY, radius, radius - 3, 0, 0, Math.PI * 2)
  ctx.strokeStyle = baseColor
  ctx.lineWidth = 2
  ctx.stroke()

  ctx.beginPath()
  ctx.ellipse(x, y + liftY - 4, radius - 8, radius - 10, 0, 0, Math.PI * 2)
  ctx.strokeStyle = isRed ? '#e85a6c' : '#4a5568'
  ctx.lineWidth = 1
  ctx.stroke()

  ctx.beginPath()
  ctx.arc(x - 8, y + liftY - 8, 5, 0, Math.PI * 2)
  ctx.fillStyle = 'rgba(255,255,255,0.4)'
  ctx.fill()

  ctx.beginPath()
  ctx.arc(x - 5, y + liftY - 5, 3, 0, Math.PI * 2)
  ctx.fillStyle = 'rgba(255,255,255,0.6)'
  ctx.fill()

  if (isSelected) {
    ctx.beginPath()
    ctx.ellipse(x, y + liftY, radius + 4, radius + 1, 0, 0, Math.PI * 2)
    ctx.strokeStyle = '#ffeb3b'
    ctx.lineWidth = 3
    ctx.stroke()

    ctx.beginPath()
    ctx.ellipse(x, y + liftY, radius + 7, radius + 4, 0, 0, Math.PI * 2)
    ctx.strokeStyle = 'rgba(255,235,59,0.3)'
    ctx.lineWidth = 6
    ctx.stroke()
  }

  ctx.save()
  ctx.font = 'bold 22px "STKaiti", "KaiTi", serif'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'

  ctx.shadowColor = 'rgba(0,0,0,0.2)'
  ctx.shadowOffsetX = 1
  ctx.shadowOffsetY = 2
  ctx.fillStyle = baseColor
  ctx.fillText(pieceNames[piece.type] || piece.type, x, y + liftY)

  ctx.restore()
}

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

function draw() {
  if (!canvas.value) return
  const ctx = canvas.value.getContext('2d')
  ctx.clearRect(0, 0, canvasWidth, canvasHeight)
  drawBoard(ctx)
  drawPieces(ctx)
}

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
    if (clickedPiece && clickedPiece.side === selectedPiece.value.piece.side) {
      selectedPiece.value = { row, col, piece: clickedPiece }
    } else {
      emit('move', {
        from: [selectedPiece.value.row, selectedPiece.value.col],
        to: [row, col],
      })
      selectedPiece.value = null
    }
  } else {
    if (clickedPiece) {
      if (props.mySide && clickedPiece.side === props.mySide) {
        selectedPiece.value = { row, col, piece: clickedPiece }
      } else if (props.canDrag) {
        selectedPiece.value = { row, col, piece: clickedPiece }
      }
    }
  }

  draw()
}

onMounted(() => {
  boardState.value = parseFen(props.fen)
  nextTick(() => draw())
})

watch(() => props.fen, (newFen) => {
  boardState.value = parseFen(newFen)
  selectedPiece.value = null
  nextTick(() => draw())
})

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
  border: 4px solid #5d3a1a;
  border-radius: 8px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.3), inset 0 2px 4px rgba(255,255,255,0.2);
  cursor: pointer;
}
</style>