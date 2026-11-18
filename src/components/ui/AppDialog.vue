<script setup>
import { ref, watch } from 'vue'

// A modal popup built on the browser's own <dialog>, which handles focus
// trapping and Escape. Used by the playlist popups.
const props = defineProps({
  open: { type: Boolean, default: false },
  title: { type: String, required: true },
  // While true the popup can't be dismissed (a save is in flight).
  busy: { type: Boolean, default: false },
  wide: { type: Boolean, default: false },
})
const emit = defineEmits(['close'])

const dialog = ref(null)
const titleId = `dialog-title-${Math.random().toString(36).slice(2, 9)}`

watch(
  () => props.open,
  (isOpen) => {
    const el = dialog.value
    if (!el) return
    if (isOpen && !el.open) el.showModal()
    if (!isOpen && el.open) el.close()
  },
  { flush: 'post' },
)

function requestClose() {
  if (!props.busy) emit('close')
}
</script>

<template>
  <dialog
    ref="dialog"
    class="dialog"
    :class="{ wide }"
    :aria-labelledby="titleId"
    @cancel.prevent="requestClose"
    @click.self="requestClose"
  >
    <div v-if="open" class="body">
      <h2 :id="titleId">{{ title }}</h2>
      <slot />
    </div>
  </dialog>
</template>

<style scoped>
.dialog {
  width: min(92vw, 460px);
  max-height: 90vh;
  padding: 0;
  border: 1px solid var(--c-border);
  border-radius: var(--radius);
  background: var(--c-surface);
  color: var(--c-text);
}

.dialog.wide {
  width: min(94vw, 560px);
}

.dialog::backdrop {
  background: rgba(17, 24, 39, 0.45);
}

.body {
  padding: 24px;
}

h2 {
  margin: 0 0 12px;
  font-size: 20px;
}
</style>