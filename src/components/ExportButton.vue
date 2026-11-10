
<script setup>
import { useLinks } from '../composables/useLinks.js'

const {
  playlists,
  selectedPlaylistId,
  canExport,
  exportZip,
  busy,
  exporting,
} = useLinks()
</script>

<template>
  <div class="export-controls">
    <select
      v-model="selectedPlaylistId"
      class="playlist-select"
      :disabled="busy || !playlists.length"
      aria-label="Select playlist to export"
    >
      <option :value="null">select playlist...</option>

      <option
        v-for="playlist in playlists"
        :key="playlist.playlist_id"
        :value="playlist.playlist_id"
      >
        {{ playlist.name }} ({{ playlist.track_count }})
      </option>
    </select>

    <button
      class="action-button"
      type="button"
      :disabled="!canExport"
      @click="exportZip"
    >
      {{ exporting ? 'exporting...' : 'export' }}
    </button>
  </div>
</template>

<style scoped>
.export-controls {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.playlist-select {
  min-width: 0;
  max-width: 220px;
  height: 72px;
  padding: 10px;
  border: 3px solid #111;
  border-radius: 0;
  background: #fff;
  color: #111;
  font: inherit;
  font-size: 16px;
}

.playlist-select:disabled {
  color: #888;
  background: #eee;
}

@media (max-width: 640px) {
  .export-controls {
    flex: 1;
  }

  .playlist-select {
    flex: 1;
    height: 60px;
    font-size: 13px;
  }
}
</style>
