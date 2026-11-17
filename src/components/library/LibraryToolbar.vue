<script setup>
const query = defineModel('query', { type: String, default: '' })

defineProps({
  selectedCount: { type: Number, default: 0 },
})
defineEmits(['delete'])
</script>

<template>
  <div class="toolbar">
    <input
      v-model="query"
      class="search"
      type="search"
      placeholder="Search songs"
      aria-label="Search songs"
    />

    <div class="actions">
      <span v-if="selectedCount" class="count" aria-live="polite">
        {{ selectedCount }} selected
      </span>

      <RouterLink :to="{ name: 'import' }" class="app-btn app-btn-primary">
        Import Music
      </RouterLink>

      <button
        class="app-btn"
        type="button"
        disabled
        title="Playlists are coming in a later update"
      >
        Add to Playlist
      </button>

      <button
        class="app-btn app-btn-danger"
        type="button"
        :disabled="!selectedCount"
        @click="$emit('delete')"
      >
        Delete Music
      </button>
    </div>
  </div>
</template>

<style scoped>
.toolbar {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 16px;
}

.search {
  width: 100%;
  min-height: 44px;
  padding: 0 16px;
  border: 1px solid var(--c-border);
  border-radius: 10px;
  background: var(--c-surface);
  color: var(--c-text);
  font: inherit;
  font-size: 15px;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.count {
  margin-right: auto;
  font-size: 14px;
  color: var(--c-muted);
}

/* Push the buttons to the right when nothing is selected. */
.actions .app-btn:first-of-type {
  margin-left: auto;
}

.count + .app-btn {
  margin-left: 0;
}
</style>