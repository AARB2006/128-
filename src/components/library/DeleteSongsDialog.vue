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
    class="dialog"
    aria-labelledby="delete-title"
    @cancel.prevent="requestCancel"
    @click.self="requestCancel"
  >
    <div class="body">
      <h2 id="delete-title">
        Delete {{ count }} {{ count === 1 ? 'song' : 'songs' }}?
      </h2>
      <p>
        {{ count === 1 ? 'This song' : 'These songs' }} will be removed from
        your library and from any playlists that contain
        {{ count === 1 ? 'it' : 'them' }}. This can't be undone.
      </p>

      <div class="buttons">
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

<style scoped>
.dialog {
  width: min(92vw, 440px);
  padding: 0;
  border: 1px solid var(--c-border);
  border-radius: var(--radius);
  background: var(--c-surface);
  color: var(--c-text);
}

.dialog::backdrop {
  background: rgba(17, 24, 39, 0.45);
}

.body {
  padding: 24px;
}

h2 {
  margin: 0 0 8px;
  font-size: 20px;
}

p {
  margin: 0 0 24px;
  color: var(--c-muted);
}

.buttons {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>