<script setup>
import { onMounted } from 'vue'
import PlaylistNameInput from '@/components/PlaylistNameInput.vue'
import LinkTextbox from '@/components/LinkTextbox.vue'
import ImportError from '@/components/ImportError.vue'
import ImportStatus from '@/components/ImportStatus.vue'
import ImportButton from '@/components/ImportButton.vue'
import ExportButton from '@/components/ExportButton.vue'
import PlaylistHistory from '@/components/PlaylistHistory.vue'
import { useLinks } from '@/composables/useLinks.js'

const { refresh } = useLinks()
onMounted(refresh)
</script>

<template>
  <main class="page-shell">
    <section class="import-panel" aria-label="YT-MP3 import panel">
      <div class="main-column">
        <PlaylistNameInput />
        <LinkTextbox />
        <ImportError />
        <ImportStatus />

        <div class="actions-row">
          <ImportButton />
          <ExportButton />
        </div>
      </div>

      <aside class="history-column">
        <PlaylistHistory />
      </aside>
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

/* 60 / 40 split: import side on the left, playlist history on the right. */
.import-panel {
  display: grid;
  grid-template-columns: 3fr 2fr;
  gap: 24px;
  width: min(100%, 1200px);
}

.main-column,
.history-column {
  min-width: 0;
}

/* The history box is pulled out of the flow and stretched over the column, so
   it is exactly as tall as the import side and scrolls inside when it's long. */
.history-column {
  position: relative;
}

.history-column > :deep(.playlist-history) {
  position: absolute;
  inset: 0;
}

.actions-row {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 16px;
  margin-top: 12px;
}

/* Narrow screens: stack, with history below the import side. */
@media (max-width: 900px) {
  .import-panel {
    grid-template-columns: 1fr;
  }

  .history-column {
    height: 360px;
  }
}

@media (max-width: 640px) {
  .page-shell {
    align-items: flex-start;
    padding: 28px 16px;
  }
}
</style>