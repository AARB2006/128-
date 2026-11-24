<!--
Confirmation popup for deleting playlists.
-->
<script setup>
import AppDialog from '@/components/ui/AppDialog.vue'

defineProps({
  open: { type: Boolean, default: false },
  count: { type: Number, default: 0 },
  // When deleting just one, its name is shown for certainty.
  name: { type: String, default: '' },
  busy: { type: Boolean, default: false },
})
const emit = defineEmits(['confirm', 'cancel'])
</script>

<template>
  <AppDialog
    :open="open"
    :title="count === 1 ? 'Delete this playlist?' : `Delete ${count} playlists?`"
    :busy="busy"
    @close="emit('cancel')"
  >
    <p class="text mt-0 mb-6 text-muted wrap-anywhere">
      <template v-if="count === 1 && name">“{{ name }}” will be deleted.</template>
      <template v-else>
        {{ count === 1 ? 'This playlist' : 'These playlists' }} will be deleted.
      </template>
      Your songs stay in your Music Library. This can't be undone.
    </p>

    <div class="buttons flex justify-end gap-2">
      <button class="app-btn" type="button" :disabled="busy" @click="emit('cancel')">
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
  </AppDialog>
</template>
