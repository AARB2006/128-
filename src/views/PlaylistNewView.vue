<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import PlaylistFields from '@/components/playlists/PlaylistFields.vue'
import { createPlaylist } from '@/services/playlistService.js'
import { checkPlaylistFields, DESCRIPTION_MAX, NAME_MAX } from '@/services/playlistRules.js'

const router = useRouter()

const name = ref('')
const description = ref('')
const busy = ref(false)
const error = ref('')

const canSubmit = computed(
  () =>
    !busy.value &&
    name.value.trim().length > 0 &&
    name.value.trim().length <= NAME_MAX &&
    description.value.trim().length <= DESCRIPTION_MAX,
)

async function onSubmit() {
  if (busy.value) return // a double click or a second Enter must not create two playlists

  const checked = checkPlaylistFields({ name: name.value, description: description.value })
  if (checked.error) {
    error.value = checked.error
    return
  }

  busy.value = true
  error.value = ''
  try {
    const created = await createPlaylist({
      name: checked.name,
      description: checked.description,
    })
    // Straight to the new playlist so songs can be added.
    router.push({ name: 'playlist', params: { playlistId: created.playlist_id } })
  } catch (e) {
    error.value = e.message || 'Could not create the playlist.'
    busy.value = false
  }
}
</script>

<template>
  <section class="app-page">
    <h1 class="app-page-title">Add Playlist</h1>

    <p class="app-muted intro mt-0 mb-5">
      Give your playlist a name. You can add songs from your Music Library once it's created.
    </p>

    <form @submit.prevent="onSubmit">
      <PlaylistFields
        v-model:name="name"
        v-model:description="description"
        :disabled="busy"
        id-prefix="new-playlist"
      />

      <p v-if="error" class="app-alert message mt-4 mb-0" role="alert">{{ error }}</p>

      <div class="actions my-4 flex flex-wrap items-center justify-between gap-2">
        <RouterLink :to="{ name: 'playlists' }" class="app-btn">Back to Playlists</RouterLink>

        <button class="app-btn app-btn-primary" type="submit" :disabled="!canSubmit">
          {{ busy ? 'Adding…' : 'Add Playlist' }}
        </button>
      </div>
    </form>
  </section>
</template>
