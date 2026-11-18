<script setup>
defineProps({
  summary: { type: Object, required: true },
})
</script>

<template>
  <div class="app-card results flex flex-col items-start gap-2" role="status">
    <p class="headline m-0 text-[18px] font-bold">{{ summary.headline }}</p>

    <p v-if="summary.duplicates" class="app-muted m-0">
      {{ summary.duplicates }}
      {{ summary.duplicates === 1 ? 'link was' : 'links were' }} already in your library
      or repeated.
    </p>

    <template v-if="summary.problems.length">
      <p class="problems-title mt-2 mb-0 font-bold text-danger">
        {{ summary.problems.length }}
        {{ summary.problems.length === 1 ? 'link' : 'links' }} could not be imported:
      </p>

      <ul class="problems m-0 flex w-full list-none flex-col gap-2 p-0">
        <li
          v-for="problem in summary.problems"
          :key="problem.line"
          class="flex flex-col gap-0.5 rounded-[10px] border border-danger-border bg-danger-bg px-3.5 py-2.5 text-[14px] text-danger"
        >
          <span>Link {{ problem.line }}: {{ problem.reason }}</span>
          <code class="text-[13px] wrap-anywhere opacity-85">{{ problem.url }}</code>
        </li>
      </ul>

      <p class="app-muted hint m-0 text-[14px]">
        Those links are back in the box above so you can fix them and try again.
      </p>
    </template>

    <RouterLink
      v-if="summary.added"
      :to="{ name: 'library' }"
      class="app-btn app-btn-primary mt-2"
    >
      View Music Library
    </RouterLink>
  </div>
</template>
