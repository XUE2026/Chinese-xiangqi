<template>
  <div class="loading-container">
    <div class="loading-content">
      <div class="page-text" :key="currentPage">
        {{ currentPageText }}
      </div>
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: progressWidth }"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'

const props = defineProps({
  pages: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['complete'])

const currentPage = ref(0)
const progressWidth = ref('0%')

const currentPageText = computed(() => {
  if (props.pages && props.pages[currentPage.value]) {
    return props.pages[currentPage.value].text
  }
  return '正在加载...'
})

onMounted(() => {
  if (!props.pages || props.pages.length === 0) {
    setTimeout(() => emit('complete'), 100)
    return
  }

  const totalPages = props.pages.length
  const durationPerPage = 1500 // 1.5秒每页

  let page = 0
  const showNextPage = () => {
    if (page < totalPages) {
      currentPage.value = page
      progressWidth.value = `${((page + 1) / totalPages) * 100}%`
      page++
      setTimeout(showNextPage, durationPerPage)
    } else {
      emit('complete')
    }
  }

  setTimeout(showNextPage, 500)
})
</script>

<style scoped>
.loading-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f5f0e6 0%, #e8dcc8 100%);
}

.loading-content {
  text-align: center;
  max-width: 500px;
  padding: 40px;
}

.page-text {
  font-size: 24px;
  color: #8b4513;
  margin-bottom: 30px;
  animation: fadeIn 0.5s ease-out;
}

.progress-bar {
  width: 300px;
  height: 6px;
  background: #ddd;
  border-radius: 3px;
  margin: 0 auto;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #8b4513, #c67d3a);
  border-radius: 3px;
  transition: width 0.3s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>