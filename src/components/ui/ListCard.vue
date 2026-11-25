<!--
One card holding a list page's search box, its table and a footer line.
-->
<script setup>
const query = defineModel('query', { type: String, default: '' })

defineProps({
  placeholder: { type: String, default: 'Search' },
})
</script>

<template>
  <div class="list-card overflow-hidden rounded-card border border-border bg-surface">
    <div
      class="list-toolbar flex flex-wrap items-center justify-between gap-3 border-b border-border p-3"
    >
      <div class="search relative max-w-[420px] min-w-0 flex-[1_1_280px]">
        <svg
          class="pointer-events-none absolute top-1/2 left-3.5 size-[18px] -translate-y-1/2 text-muted"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
          aria-hidden="true"
        >
          <circle cx="11" cy="11" r="7" />
          <path d="M20 20l-3.5-3.5" />
        </svg>
        <input
          v-model="query"
          class="font-inherit min-h-11 w-full rounded-[10px] border border-border bg-bg py-0 pr-3.5 pl-[42px] text-[15px] text-text placeholder:text-muted"
          type="search"
          :placeholder="placeholder"
          :aria-label="placeholder"
        />
      </div>
      <div class="tools flex flex-wrap items-center gap-2">
        <slot name="tools" />
      </div>
    </div>

    <!-- The table (or a message when there is nothing to show). Wide tables
         scroll sideways inside the card on small screens. -->
    <div class="list-body overflow-x-auto">
      <slot />
    </div>

    <div
      v-if="$slots.footer"
      class="list-footer flex flex-wrap justify-between gap-3 border-t border-border px-4 py-3 text-[13px] text-muted"
    >
      <slot name="footer" />
    </div>
  </div>
</template>
