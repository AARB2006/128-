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
    class="dialog max-h-[90vh] w-[min(92vw,460px)] rounded-card border border-border bg-surface p-0 text-text backdrop:bg-[rgba(17,24,39,0.45)] [&.wide]:w-[min(94vw,560px)]"
    :class="{ wide }"
    :aria-labelledby="titleId"
    @cancel.prevent="requestClose"
    @click.self="requestClose"
  >
    <div v-if="open" class="body p-6">
      <h2 :id="titleId" class="mt-0 mb-3 text-[20px]">{{ title }}</h2>
      <slot />
    </div>
  </dialog>
</template>