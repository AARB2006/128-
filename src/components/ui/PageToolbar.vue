<script setup>
// The search bar with a row of buttons under it, laid out like the Music
// Library's. Buttons go in the `left` and `right` slots.
const query = defineModel('query', { type: String, default: '' })

defineProps({
  placeholder: { type: String, default: 'Search' },
})
</script>

<template>
  <div class="toolbar">
    <input
      v-model="query"
      class="search"
      type="search"
      :placeholder="placeholder"
      :aria-label="placeholder"
    />

    <div class="actions">
      <div class="actions-left"><slot name="left" /></div>
      <div class="actions-right"><slot name="right" /></div>
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
</style>