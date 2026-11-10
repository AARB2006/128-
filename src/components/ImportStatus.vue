
<script setup>
import { useLinks } from '../composables/useLinks.js'

const { status, exporting } = useLinks()
</script>

<template>
  <div
    class="import-status"
    :class="{ exporting }"
    role="status"
    aria-live="polite"
    :aria-busy="exporting"
  >
    <span>{{ status || 'STATUS OF IMPORT...' }}</span>

    <div v-if="exporting" class="progress-track">
      <div class="progress-indicator"></div>
    </div>
  </div>
</template>

<style scoped>
.import-status {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  min-height: 48px;
  padding: 8px 14px;
  border: 3px solid #111;
  background: #a89a9a;
  color: #111;
  text-align: center;
  font-size: 20px;
  line-height: 1.3;
}

.import-status.exporting {
  background: #d6caca;
}

.progress-track {
  position: relative;
  width: min(100%, 280px);
  height: 7px;
  overflow: hidden;
  background: #fff;
  border: 1px solid #111;
}

.progress-indicator {
  position: absolute;
  top: 0;
  left: -35%;
  width: 35%;
  height: 100%;
  background: #111;
  animation: export-progress 1.2s ease-in-out infinite;
}

@keyframes export-progress {
  0% {
    left: -35%;
  }

  100% {
    left: 100%;
  }
}

@media (max-width: 640px) {
  .import-status {
    min-height: 46px;
    font-size: 15px;
  }
}
</style>
