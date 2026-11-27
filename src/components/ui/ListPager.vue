<!--
Previous / Next buttons and "Page 2 of 5", for a list card's footer.
-->
<script setup>
defineProps({
  page: { type: Number, required: true },
  pageCount: { type: Number, required: true },
  label: { type: String, default: 'Pages' },
})
defineEmits(['go'])

const btn =
  'font-inherit inline-flex size-8 cursor-pointer items-center justify-center rounded-[8px] border border-border bg-transparent text-text ' +
  'hover:bg-hover disabled:cursor-default disabled:opacity-40 disabled:hover:bg-transparent'
</script>

<template>
  <nav class="pager flex items-center gap-2" :aria-label="label">
    <button
      :class="btn"
      type="button"
      :disabled="page <= 1"
      aria-label="Previous page"
      @click="$emit('go', page - 1)"
    >
      <svg class="size-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M15 18l-6-6 6-6" />
      </svg>
    </button>
    <span class="page-label min-w-[92px] text-center text-[13px] text-muted" aria-live="polite">
      Page {{ page }} of {{ pageCount }}
    </span>
    <button
      :class="btn"
      type="button"
      :disabled="page >= pageCount"
      aria-label="Next page"
      @click="$emit('go', page + 1)"
    >
      <svg class="size-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M9 18l6-6-6-6" />
      </svg>
    </button>
  </nav>
</template>
