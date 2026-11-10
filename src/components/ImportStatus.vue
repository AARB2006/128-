<script setup>
import { useLinks } from '../composables/useLinks.js'

const { status } = useLinks()
</script>

<template>
  <div class="import-status" role="status" aria-live="polite">
    {{ status || 'STATUS OF IMPORT...' }}
  </div>
</template>

<style scoped>
.import-status {
  display: flex;
  align-items: center;
  justify-content: center;
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

@media (max-width: 640px) {
  .import-status {
    min-height: 46px;
    font-size: 15px;
  }
}
</style>
