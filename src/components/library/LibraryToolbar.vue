<script setup>
const query = defineModel('query', { type: String, default: '' })

defineProps({
  selectedCount: { type: Number, default: 0 },
})
defineEmits(['delete', 'add-to-playlist'])
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
      <div class="actions-left">
        <RouterLink :to="{ name: 'import' }" class="app-btn app-btn-primary">
          Import Music
        </RouterLink>
      </div>

      <div class="actions-right">
        <span v-if="selectedCount" class="count" aria-live="polite">
          {{ selectedCount }} selected
        </span>

        <button
          class="app-btn"
          type="button"
          :disabled="!selectedCount"
          @click="$emit('add-to-playlist')"
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
  justify-content: space-between;
  gap: 8px;
}

.actions-left,
.actions-right {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.count {
  font-size: 14px;
  color: var(--c-muted);
}
</style>