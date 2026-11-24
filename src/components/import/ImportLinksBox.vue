<!--
Text box where links to import are typed or pasted.
-->
<script setup>
const text = defineModel({ type: String, default: '' })

defineProps({
  count: { type: Number, default: 0 },
  max: { type: Number, default: 10 },
  overLimit: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
})
</script>

<template>
  <div
    class="links-box relative rounded-card border border-border bg-surface focus-within:outline-3 focus-within:outline-offset-2 focus-within:outline-focus [&.over]:border-danger"
    :class="{ over: overLimit, disabled }"
  >
    <label class="visually-hidden" for="import-links">YouTube video links</label>

    <textarea
      id="import-links"
      v-model="text"
      class="font-inherit block min-h-[280px] w-full resize-y rounded-card border-0 bg-transparent px-4.5 pt-4 pb-12 text-[16px] leading-[1.5] text-text outline-0 placeholder:text-muted disabled:cursor-not-allowed disabled:text-muted"
      :disabled="disabled"
      placeholder="Paste YouTube links here, one per line..."
      spellcheck="false"
    ></textarea>

    <span
      class="counter absolute right-4 bottom-3 text-[14px] text-muted tabular-nums [&.over]:font-bold [&.over]:text-danger"
      :class="{ over: overLimit }"
      aria-live="polite"
    >
      {{ count }}/{{ max }}
    </span>
  </div>
</template>
