<script setup>
const query = defineModel('query', { type: String, default: '' })

defineProps({
  selectedCount: { type: Number, default: 0 },
})
defineEmits(['delete', 'add-to-playlist'])
</script>

<template>
  <div class="toolbar mb-4 flex flex-col gap-3">
    <input
      v-model="query"
      class="search font-inherit min-h-11 w-full rounded-[10px] border border-border bg-surface px-4 py-0 text-[15px] text-text"
      type="search"
      placeholder="Search songs"
      aria-label="Search songs"
    />

    <div class="actions flex flex-wrap items-center justify-between gap-2">
      <div class="actions-left flex flex-wrap items-center gap-2">
        <RouterLink :to="{ name: 'import' }" class="app-btn app-btn-primary">
          Import Music
        </RouterLink>
      </div>

      <div class="actions-right flex flex-wrap items-center gap-2">
        <span v-if="selectedCount" class="count text-[14px] text-muted" aria-live="polite">
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
