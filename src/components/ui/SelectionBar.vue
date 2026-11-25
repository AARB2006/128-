<!--
"N selected" with the actions for the selection and a button to clear it.
-->
<script setup>
defineProps({
  count: { type: Number, required: true },
})
defineEmits(['clear'])
</script>

<template>
  <div
    class="selection-bar flex flex-wrap items-center gap-2 rounded-[12px] bg-accent-soft py-1 pr-1 pl-3.5"
    role="group"
    aria-label="Selected items"
  >
    <span class="count text-[14px] font-semibold text-text" aria-live="polite">
      {{ count }} selected
    </span>
    <slot />
    <button
      class="clear inline-flex size-9 cursor-pointer items-center justify-center rounded-[8px] border-0 bg-transparent text-muted hover:bg-hover hover:text-text"
      type="button"
      aria-label="Clear selection"
      @click="$emit('clear')"
    >
      <svg
        class="size-4"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        aria-hidden="true"
      >
        <path d="M6 6l12 12M18 6L6 18" />
      </svg>
    </button>
  </div>
</template>
