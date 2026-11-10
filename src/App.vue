<script setup>
import { onMounted } from 'vue'
import PlaylistNameInput from './components/PlaylistNameInput.vue'
import LinkTextbox from './components/LinkTextbox.vue'
import ImportError from './components/ImportError.vue'
import ImportStatus from './components/ImportStatus.vue'
import LinkList from './components/LinkList.vue'
import ImportButton from './components/ImportButton.vue'
import ExportButton from './components/ExportButton.vue'
import { useLinks } from './composables/useLinks.js'

const { refresh } = useLinks()
onMounted(refresh)
</script>

<template>
  <main class="page-shell">
    <section class="import-panel" aria-label="YT-MP3 import panel">
      <PlaylistNameInput />
      <LinkTextbox />
      <ImportError />
      <ImportStatus />
      <LinkList />

      <div class="actions-row">
        <ImportButton />
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