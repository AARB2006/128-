<script setup>
defineProps({
  summary: { type: Object, required: true },
})
</script>

<template>
  <div class="app-card results" role="status">
    <p class="headline">{{ summary.headline }}</p>

    <p v-if="summary.duplicates" class="app-muted">
      {{ summary.duplicates }}
      {{ summary.duplicates === 1 ? 'link was' : 'links were' }} already in your library
      or repeated.
    </p>

    <template v-if="summary.problems.length">
      <p class="problems-title">
        {{ summary.problems.length }}
        {{ summary.problems.length === 1 ? 'link' : 'links' }} could not be imported:
      </p>

      <ul class="problems">
        <li v-for="problem in summary.problems" :key="problem.line">
          <span>Link {{ problem.line }}: {{ problem.reason }}</span>
          <code>{{ problem.url }}</code>
        </li>
      </ul>

      <p class="app-muted hint">
        Those links are back in the box above so you can fix them and try again.
      </p>
    </template>

    <RouterLink
      v-if="summary.added"
      :to="{ name: 'library' }"
      class="app-btn app-btn-primary"
    >
      View Music Library
    </RouterLink>
  </div>
</template>

<style scoped>
.results {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
}

p {
  margin: 0;
}

.headline {
  font-size: 18px;
  font-weight: bold;
}

.problems-title {
  margin-top: 8px;
  color: var(--c-danger);
  font-weight: bold;
}

.problems {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
  margin: 0;
  padding: 0;
  list-style: none;
}

.problems li {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 10px 14px;
  border: 1px solid #fecdca;
  border-radius: 10px;
  background: var(--c-danger-bg);
  color: var(--c-danger);
  font-size: 14px;
}

code {
  overflow-wrap: anywhere;
  font-size: 13px;
  opacity: 0.85;
}

.hint {
  font-size: 14px;
}

.results .app-btn {
  margin-top: 8px;
}
</style>