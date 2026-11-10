<script setup>
import { useLinks } from '../composables/useLinks.js'

const { links, max } = useLinks()
</script>

<template>
  <section class="link-list" aria-label="Imported links">
    <header class="list-header">
      <span>playlist</span>
      <span class="list-count">{{ links.length }}/{{ max }}</span>
    </header>

    <p v-if="!links.length" class="empty">No links imported yet.</p>

    <ol v-else class="items">
      <li v-for="link in links" :key="link.id" class="item">
        <span class="position">{{ link.position }}</span>
        <span class="details">
          <span class="title">{{ link.title }}</span>
          <span class="url">{{ link.url }}</span>
        </span>
      </li>
    </ol>
  </section>
</template>

<style scoped>
.link-list {
  margin-top: 12px;
  border: 3px solid #111;
  background: #fff;
}

.list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 14px;
  border-bottom: 3px solid #111;
  font-size: 20px;
}

.list-count {
  font-variant-numeric: tabular-nums;
}

.empty {
  margin: 0;
  padding: 18px 14px;
  color: #525151;
  text-align: center;
  font-size: 18px;
}

.items {
  max-height: 320px;
  margin: 0;
  padding: 0;
  overflow-y: auto;
  list-style: none;
}

.item {
  display: grid;
  grid-template-columns: 2.5ch 1fr;
  gap: 14px;
  padding: 10px 14px;
  border-bottom: 1px solid #ccc;
}

.item:last-child {
  border-bottom: 0;
}

.position {
  font-size: 18px;
  font-variant-numeric: tabular-nums;
  text-align: right;
}

.details {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.title {
  font-size: 18px;
  overflow-wrap: anywhere;
}

.url {
  color: #525151;
  font-size: 14px;
  overflow-wrap: anywhere;
}

@media (max-width: 640px) {
  .list-header {
    font-size: 16px;
  }

  .title {
    font-size: 16px;
  }
}
</style>
