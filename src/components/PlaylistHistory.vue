<script setup>
import { useLinks } from '../composables/useLinks.js'

// Placeholder for now: shows the flat list of imported links. Later this will
// group songs under their playlist names. There is no limit on history size.
const { links } = useLinks()
</script>

<template>
  <section class="playlist-history" aria-label="Playlist history">
    <header class="history-header">playlist history</header>

    <p v-if="!links.length" class="empty">No history yet.</p>

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
.playlist-history {
  display: flex;
  flex-direction: column;
  height: 100%;
  border: 3px solid #111;
  background: #fff;
}

.history-header {
  padding: 8px 14px;
  border-bottom: 3px solid #111;
  font-size: 20px;
}

.empty {
  margin: 0;
  padding: 18px 14px;
  color: #525151;
  text-align: center;
  font-size: 18px;
}

/* Fills the box and scrolls inside it, so a long history never stretches the page. */
.items {
  flex: 1;
  min-height: 0;
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
  .history-header {
    font-size: 16px;
  }

  .title {
    font-size: 16px;
  }
}
</style>