<!--
Search bar with button slots, shared by list pages.
-->
<script setup>
// The search bar with a row of buttons under it, laid out like the Music
// Library's. Buttons go in the `left` and `right` slots.
const query = defineModel('query', { type: String, default: '' })

defineProps({
  placeholder: { type: String, default: 'Search' },
})
</script>

<template>
  <div class="toolbar mb-4 flex flex-col gap-3">
    <input
      v-model="query"
      class="search font-inherit min-h-11 w-full rounded-[10px] border border-border bg-surface px-4 py-0 text-[15px] text-text"
      type="search"
      :placeholder="placeholder"
      :aria-label="placeholder"
    />

    <div class="actions flex flex-wrap items-center justify-between gap-2">
      <div class="actions-left flex flex-wrap items-center gap-2"><slot name="left" /></div>
      <div class="actions-right flex flex-wrap items-center gap-2"><slot name="right" /></div>
    </div>
  </div>
</template>