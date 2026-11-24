<!--
Confirmation popup for deleting one export or the whole history.
-->
<script setup>
import AppDialog from '@/components/ui/AppDialog.vue'

defineProps({
  open: { type: Boolean, default: false },
  // true: clear the whole history. false: delete just one export.
  all: { type: Boolean, default: false },
  // When deleting one, its playlist name is shown for certainty.
  name: { type: String, default: '' },
  busy: { type: Boolean, default: false },
  error: { type: String, default: '' },
})
const emit = defineEmits(['confirm', 'cancel'])
</script>

<template>
  <AppDialog
    :open="open"
    :title="all ? 'Delete export history?' : 'Delete this export?'"
    :busy="busy"
    @close="emit('cancel')"
  >
    <p class="text mt-0 mb-6 text-muted wrap-anywhere">
      <template v-if="all">
        Every export will be removed from this list and its ZIP file deleted. An export that
        is still running isn't affected.
      </template>
      <template v-else>
        <template v-if="name">The export of “{{ name }}” will</template>
        <template v-else>This export will</template>
        be removed from this list and its ZIP file deleted.
      </template>
      Your playlists and songs aren't affected. This can't be undone.
    </p>

    <p v-if="error" class="app-alert" role="alert">{{ error }}</p>

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
