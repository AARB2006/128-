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
  <div class="links-box" :class="{ over: overLimit, disabled }">
    <label class="visually-hidden" for="import-links">YouTube video links</label>

    <textarea
      id="import-links"
      v-model="text"
      :disabled="disabled"
      placeholder="Paste YouTube links here, one per line..."
      spellcheck="false"
    ></textarea>

    <span class="counter" :class="{ over: overLimit }" aria-live="polite">
      {{ count }}/{{ max }}
    </span>
  </div>
</template>

<style scoped>
.links-box {
  position: relative;
  border: 1px solid var(--c-border);
  border-radius: var(--radius);
  background: var(--c-surface);
}

.links-box:focus-within {
  outline: 3px solid #98a2b3;
  outline-offset: 2px;
}

.links-box.over {
  border-color: var(--c-danger);
}

textarea {
  display: block;
  width: 100%;
  min-height: 280px;
  padding: 16px 18px 48px;
  border: 0;
  border-radius: var(--radius);
  outline: 0;
  resize: vertical;
  background: transparent;
  color: var(--c-text);
  font: inherit;
  font-size: 16px;
  line-height: 1.5;
}

textarea::placeholder {
  color: var(--c-muted);
}

textarea:disabled {
  color: var(--c-muted);
  cursor: not-allowed;
}

.counter {
  position: absolute;
  right: 16px;
  bottom: 12px;
  font-size: 14px;
  font-variant-numeric: tabular-nums;
  color: var(--c-muted);
}

.counter.over {
  color: var(--c-danger);
  font-weight: bold;
}

.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  margin: -1px;
  padding: 0;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
</style>