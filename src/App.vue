<script setup>
import LinkTextbox from './components/LinkTextbox.vue'
import ImportError from './components/ImportError.vue'
import ImportStatus from './components/ImportStatus.vue'
import ExportButton from './components/ExportButton.vue'
</script>

<template>
  <main class="page-shell">
    <section class="import-panel" aria-label="YT-MP3 import panel">
      <LinkTextbox />
      <ImportError />
      <ImportStatus />

      <div class="actions-row">
        <ExportButton />
      </div>
    </section>
  </main>
</template>

<style scoped>
.page-shell {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
}

.import-panel {
  width: min(100%, 1024px);
}

.actions-row {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 16px;
  margin-top: 12px;
}

@media (max-width: 640px) {
  .page-shell {
    align-items: flex-start;
    padding: 28px 16px;
  }
}
</style>
