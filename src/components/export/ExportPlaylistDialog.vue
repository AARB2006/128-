<script setup>
import { computed, ref, watch } from 'vue'
import AppDialog from '@/components/ui/AppDialog.vue'
import { MAX_EXPORT_SONGS } from '@/services/exportService.js'
import { useExportJob } from '@/composables/useExportJob.js'

// Use case B8, steps 3-4: show the export options, then start.
// Cancel closes without contacting the server (alternative flow A3).
const props = defineProps({
  open: { type: Boolean, default: false },
  // { playlist_id, name, song_count }
  playlist: { type: Object, default: null },
})
const emit = defineEmits(['close'])

const { start, busy } = useExportJob()

const starting = ref(false)
const error = ref('')

watch(
  () => props.open,
  (isOpen) => {
    if (isOpen) error.value = ''
  },
)

const count = computed(() => props.playlist?.song_count ?? 0)
const tooMany = computed(() => count.value > MAX_EXPORT_SONGS)
const canExport = computed(
  () => !starting.value && !busy.value && count.value > 0 && !tooMany.value,
)

async function onExport() {
  if (!canExport.value) return
  starting.value = true
  error.value = ''
  try {
    await start(props.playlist)
    emit('close') // the progress card takes over from here
  } catch (e) {
    error.value = e.message || 'The export could not be started.'
  } finally {
    starting.value = false
  }
}
</script>

<template>
  <AppDialog :open="open" title="Export playlist" :busy="starting" @close="emit('close')">
    <template v-if="playlist">
      <p class="summary">
        <strong class="name">{{ playlist.name }}</strong>
        <span class="app-muted">· {{ count }} {{ count === 1 ? 'song' : 'songs' }}</span>
      </p>

      <fieldset class="format">
        <legend>Format</legend>
        <label class="option">
          <input type="radio" name="export-format" value="zip" checked />
          <span>
            <span class="option-title">ZIP archive (.zip)</span>
            <span class="option-help app-muted">
              One file with an MP3 for each song. Unzip it, then copy the folder to a USB
              drive.
            </span>
          </span>
        </label>
      </fieldset>

      <p class="note app-muted">
        Songs are numbered in playlist order. Songs that can't be downloaded are skipped
        and listed when the export finishes. Your playlist and library aren't changed.
      </p>

      <p v-if="count === 0" class="app-alert">Add songs to this playlist to export it.</p>
      <p v-else-if="tooMany" class="app-alert">
        Playlists with more than {{ MAX_EXPORT_SONGS }} songs can't be exported yet.
      </p>
      <p v-else-if="busy && !starting" class="app-alert">
        Another export is running. Wait for it to finish.
      </p>
      <p v-if="error" class="app-alert" role="alert">{{ error }}</p>

      <div class="buttons">
        <button class="app-btn" type="button" :disabled="starting" @click="emit('close')">
          Cancel
        </button>
        <button
          class="app-btn app-btn-primary"
          type="button"
          :disabled="!canExport"
          @click="onExport"
        >
          {{ starting ? 'Starting…' : 'Export' }}
        </button>
      </div>
    </template>
  </AppDialog>
</template>

<style scoped>
.summary {
  margin: 0 0 16px;
  overflow-wrap: anywhere;
}

.name {
  margin-right: 4px;
}

.format {
  margin: 0 0 16px;
  padding: 0;
  border: 0;
}

legend {
  margin-bottom: 8px;
  padding: 0;
  font-size: 13px;
  font-weight: bold;
  color: var(--c-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.option {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 14px;
  border: 1px solid var(--c-accent);
  border-radius: 10px;
  background: var(--c-surface);
  cursor: pointer;
}

.option input {
  width: 18px;
  height: 18px;
  margin: 2px 0 0;
  accent-color: var(--c-accent);
}

.option-title {
  display: block;
  font-weight: bold;
}

.option-help {
  display: block;
  margin-top: 2px;
  font-size: 14px;
}

.note {
  margin: 0 0 20px;
  font-size: 14px;
}

.buttons {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
