<!--
Popup to choose which playlist receives the selected songs.
-->
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

    <div v-else-if="!playlists.length" class="empty flex flex-col items-start gap-3">
      <p class="app-muted m-0">You don't have any playlists yet.</p>
      <RouterLink :to="{ name: 'playlist-new' }" class="app-btn app-btn-primary">
        Add Playlist
      </RouterLink>
    </div>

    <fieldset
      v-else
      class="choices m-0 max-h-[min(48vh,340px)] overflow-y-auto rounded-[10px] border border-border p-0"
      :disabled="busy"
    >
      <legend class="visually-hidden">Choose a playlist</legend>
      <label
        v-for="playlist in playlists"
        :key="playlist.playlist_id"
        class="choice flex cursor-pointer items-center gap-3 border-t border-border p-3 first-of-type:border-t-0 [&.selected]:bg-selected"
        :class="{ selected: chosenId === playlist.playlist_id }"
      >
        <input
          v-model="chosenId"
          class="size-[18px] shrink-0 cursor-pointer"
          type="radio"
          name="playlist"
          :value="playlist.playlist_id"
        />
        <span class="name min-w-0 flex-1 font-bold wrap-anywhere">{{ playlist.name }}</span>
        <span class="songs text-[13px] whitespace-nowrap text-muted">
          {{ playlist.song_count }} {{ playlist.song_count === 1 ? 'song' : 'songs' }}
        </span>
      </label>
    </fieldset>

    <p v-if="error" class="app-alert message mt-4 mb-0" role="alert">{{ error }}</p>

    <div class="buttons mt-5 flex justify-end gap-2">
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
