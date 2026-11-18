<script setup>
import { ref, watch } from 'vue'
import AppDialog from '@/components/ui/AppDialog.vue'

// The Music Library's "Add to Playlist": choose which playlist gets the
// ticked songs.
const props = defineProps({
  open: { type: Boolean, default: false },
  count: { type: Number, default: 0 }, // how many songs are being added
  playlists: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  loadError: { type: String, default: '' },
  busy: { type: Boolean, default: false },
  error: { type: String, default: '' },
})
const emit = defineEmits(['choose', 'cancel', 'retry'])

const chosenId = ref('')

watch(
  () => props.open,
  (isOpen) => {
    if (isOpen) chosenId.value = ''
  },
)
</script>

<template>
  <AppDialog
    :open="open"
    :title="`Add ${count} ${count === 1 ? 'song' : 'songs'} to a playlist`"
    :busy="busy"
    @close="emit('cancel')"
  >
    <p v-if="loading" class="app-muted">Loading your playlists…</p>

    <div v-else-if="loadError" class="app-alert" role="alert">
      <span>{{ loadError }}</span>
      <button class="app-btn" type="button" @click="emit('retry')">Try again</button>
    </div>

    <div v-else-if="!playlists.length" class="empty">
      <p class="app-muted">You don't have any playlists yet.</p>
      <RouterLink :to="{ name: 'playlist-new' }" class="app-btn app-btn-primary">
        Add Playlist
      </RouterLink>
    </div>

    <fieldset v-else class="choices" :disabled="busy">
      <legend class="visually-hidden">Choose a playlist</legend>
      <label
        v-for="playlist in playlists"
        :key="playlist.playlist_id"
        class="choice"
        :class="{ selected: chosenId === playlist.playlist_id }"
      >
        <input v-model="chosenId" type="radio" name="playlist" :value="playlist.playlist_id" />
        <span class="name">{{ playlist.name }}</span>
        <span class="songs">
          {{ playlist.song_count }} {{ playlist.song_count === 1 ? 'song' : 'songs' }}
        </span>
      </label>
    </fieldset>

    <p v-if="error" class="app-alert message" role="alert">{{ error }}</p>

    <div class="buttons">
      <button class="app-btn" type="button" :disabled="busy" @click="emit('cancel')">
        Cancel
      </button>
      <button
        class="app-btn app-btn-primary"
        type="button"
        :disabled="busy || !chosenId"
        @click="emit('choose', chosenId)"
      >
        {{ busy ? 'Adding…' : 'Add to Playlist' }}
      </button>
    </div>
  </AppDialog>
</template>

<style scoped>
.empty {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 12px;
}

.empty p {
  margin: 0;
}

.choices {
  max-height: min(48vh, 340px);
  margin: 0;
  padding: 0;
  overflow-y: auto;
  border: 1px solid var(--c-border);
  border-radius: 10px;
}

.choice {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-top: 1px solid var(--c-border);
  cursor: pointer;
}

.choice:first-of-type {
  border-top: 0;
}

.choice.selected {
  background: var(--c-selected);
}

.name {
  flex: 1;
  min-width: 0;
  font-weight: bold;
  overflow-wrap: anywhere;
}

.songs {
  font-size: 13px;
  color: var(--c-muted);
  white-space: nowrap;
}

input[type='radio'] {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  cursor: pointer;
}

.message {
  margin: 16px 0 0;
}

.buttons {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 20px;
}

.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  border: 0;
}
</style>