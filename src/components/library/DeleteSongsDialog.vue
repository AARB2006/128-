<!--
Confirmation popup for deleting songs from the library.
-->
<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  count: { type: Number, default: 0 },
  busy: { type: Boolean, default: false },
})
const emit = defineEmits(['confirm', 'cancel'])

// Uses the browser's built-in <dialog>, which handles focus and Escape.
const dialog = ref(null)

watch(
  () => props.open,
  (isOpen) => {
    const el = dialog.value
    if (!el) return
    if (isOpen && !el.open) el.showModal()
    if (!isOpen && el.open) el.close()
  },
)

function requestCancel() {
  if (!props.busy) emit('cancel')
}
</script>

<template>
  <dialog
    ref="dialog"
    class="dialog w-[min(92vw,440px)] rounded-card border border-border bg-surface p-0 text-text backdrop:bg-[rgba(0,0,0,0.65)]"
    aria-labelledby="delete-title"
    @cancel.prevent="requestCancel"
    @click.self="requestCancel"
  >
    <div class="body p-6">
      <h2 id="delete-title" class="mt-0 mb-2 text-[20px]">
        Delete {{ count }} {{ count === 1 ? 'song' : 'songs' }}?
      </h2>
      <p class="mt-0 mb-6 text-muted">
        {{ count === 1 ? 'This song' : 'These songs' }} will be removed from
        your library and from any playlists that contain
        {{ count === 1 ? 'it' : 'them' }}. This can't be undone.
      </p>

      <div class="buttons flex justify-end gap-2">
        <button class="app-btn" type="button" :disabled="busy" @click="requestCancel">
          Cancel
        </button>
        <button
          class="app-btn app-btn-danger-solid"
          type="button"
          :disabled="busy"
          @click="emit('confirm')"
        >
          {{ busy ? 'Deleting…' : 'Delete' }}
        </button>
      </div>
    </div>
  </dialog>
</template>
