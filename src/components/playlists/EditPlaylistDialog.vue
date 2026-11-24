<!--
Popup to edit a playlist's name and description.
-->
<script setup>
import { ref, watch } from 'vue'
import AppDialog from '@/components/ui/AppDialog.vue'
import PlaylistFields from './PlaylistFields.vue'
import { checkPlaylistFields } from '@/services/playlistRules.js'

// Opened by clicking the playlist's name or description. Nothing is saved
// until the user presses Save; Cancel (or Escape) throws the edits away.
const props = defineProps({
  open: { type: Boolean, default: false },
  playlist: { type: Object, default: null },
  // Which field the cursor starts in: the one that was clicked.
  focus: { type: String, default: 'name' },
  busy: { type: Boolean, default: false },
  error: { type: String, default: '' },
})
const emit = defineEmits(['save', 'cancel'])

const name = ref('')
const description = ref('')
const problem = ref('')

// Start from the saved values every time the popup opens.
watch(
  () => props.open,
  (isOpen) => {
    if (!isOpen) return
    name.value = props.playlist?.name ?? ''
    description.value = props.playlist?.description ?? ''
    problem.value = ''
  },
  { immediate: true },
)

function onSubmit() {
  const checked = checkPlaylistFields({ name: name.value, description: description.value })
  if (checked.error) {
    problem.value = checked.error
    return
  }
  problem.value = ''
  emit('save', { name: checked.name, description: checked.description })
}
</script>

<template>
  <AppDialog :open="open" title="Edit playlist" :busy="busy" wide @close="emit('cancel')">
    <form @submit.prevent="onSubmit">
      <PlaylistFields
        v-model:name="name"
        v-model:description="description"
        :focus="focus"
        :disabled="busy"
        id-prefix="edit-playlist"
      />

      <p v-if="problem || error" class="app-alert message mt-4 mb-0" role="alert">
        {{ problem || error }}
      </p>

      <div class="buttons mt-5 flex justify-end gap-2">
        <button class="app-btn" type="button" :disabled="busy" @click="emit('cancel')">
          Cancel
        </button>
        <button class="app-btn app-btn-primary" type="submit" :disabled="busy">
          {{ busy ? 'Saving…' : 'Save' }}
        </button>
      </div>
    </form>
  </AppDialog>
</template>
