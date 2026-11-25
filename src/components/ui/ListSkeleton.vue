<!--
A loading placeholder shaped like ListCard: search box, header and rows.
-->
<script setup>
defineProps({
  // What screen readers hear while it shows, e.g. "Loading your songs".
  label: { type: String, default: 'Loading' },
  rows: { type: Number, default: 5 },
  // The square at the start of each row: a song thumbnail, a playlist tile, or nothing.
  lead: { type: String, default: 'thumb' }, // thumb | tile | none
  // Widths of the narrow columns after the main one, e.g. ['90px', '150px'].
  columns: { type: Array, default: () => [] },
  checkbox: { type: Boolean, default: true },
})

// Vary the title lengths so the rows don't look stamped out.
const titleWidths = ['62%', '44%', '55%', '38%', '50%', '58%', '41%', '47%']
</script>

<template>
  <div
    class="list-skeleton overflow-hidden rounded-card border border-border bg-surface"
    role="status"
    aria-live="polite"
  >
    <span class="visually-hidden">{{ label }}…</span>

    <div class="flex items-center gap-3 border-b border-border p-3" aria-hidden="true">
      <span class="app-skeleton h-11 w-full max-w-[420px] rounded-[10px]"></span>
    </div>

    <div class="bg-head px-4 py-3.5" aria-hidden="true">
      <span class="app-skeleton h-3 w-24"></span>
    </div>

    <div
      v-for="(_, index) in rows"
      :key="index"
      class="flex items-center gap-4 border-t border-border px-4 py-3"
      aria-hidden="true"
    >
      <span v-if="checkbox" class="app-skeleton size-[18px] shrink-0 rounded-[4px]"></span>
      <span
        v-if="lead === 'thumb'"
        class="app-skeleton h-10 w-[72px] shrink-0"
      ></span>
      <span
        v-else-if="lead === 'tile'"
        class="app-skeleton size-10 shrink-0 rounded-[10px]"
      ></span>
      <span class="flex min-w-0 flex-1 flex-col gap-2">
        <span class="app-skeleton h-3.5" :style="{ width: titleWidths[index % titleWidths.length] }"></span>
        <span class="app-skeleton h-3 w-[28%]"></span>
      </span>
      <span
        v-for="(width, col) in columns"
        :key="col"
        class="shrink-0 phone:hidden"
        :style="{ width }"
      >
        <span class="app-skeleton h-3 w-3/4"></span>
      </span>
    </div>
  </div>
</template>
