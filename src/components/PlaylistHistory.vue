
<script setup>
import { useLinks } from '../composables/useLinks.js'

const { playlists } = useLinks()
</script>

<template>
  <section class="playlist-history" aria-label="Playlist history">
    <header class="history-header">playlist history</header>

    <p v-if="!playlists.length" class="empty">
      No playlists yet.
    </p>

    <div v-else class="playlist-list">
      <section
        v-for="playlist in playlists"
        :key="playlist.playlist_id"
        class="playlist-item"
      >
        <header class="playlist-heading">
          <span class="playlist-name">{{ playlist.name }}</span>
          <span class="track-count">
            {{ playlist.track_count }}
            {{ playlist.track_count === 1 ? 'track' : 'tracks' }}
          </span>
        </header>

        <ol class="tracks">
          <li
            v-for="track in playlist.tracks"
            :key="track.song_id"
            class="track"
          >
            <span class="position">{{ track.position }}</span>

            <span class="details">
              <span class="title">{{ track.title }}</span>
              <span class="url">{{ track.source_url }}</span>
            </span>
          </li>
        </ol>
      </section>
    </div>
  </section>
</template>

<style scoped>
.playlist-history {
  display: flex;
  flex-direction: column;
  height: 100%;
  border: 3px solid #111;
  background: #fff;
}

.history-header {
  flex-shrink: 0;
  padding: 8px 14px;
  border-bottom: 3px solid #111;
  font-size: 20px;
}

.empty {
  margin: 0;
  padding: 18px 14px;
  color: #525151;
  text-align: center;
  font-size: 18px;
}

.playlist-list {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}

.playlist-item {
  border-bottom: 2px solid #111;
}

.playlist-item:last-child {
  border-bottom: 0;
}

.playlist-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 10px 14px;
  background: #eee;
}

.playlist-name {
  min-width: 0;
  font-size: 18px;
  overflow-wrap: anywhere;
}

.track-count {
  flex-shrink: 0;
  color: #525151;
  font-size: 13px;
}

.tracks {
  margin: 0;
  padding: 0;
  list-style: none;
}

.track {
  display: grid;
  grid-template-columns: 2.5ch 1fr;
  gap: 14px;
  padding: 10px 14px;
  border-top: 1px solid #ccc;
}

.position {
  font-size: 18px;
  font-variant-numeric: tabular-nums;
  text-align: right;
}

.details {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.title {
  font-size: 16px;
  overflow-wrap: anywhere;
}

.url {
  color: #525151;
  font-size: 12px;
  overflow-wrap: anywhere;
}

@media (max-width: 640px) {
  .history-header {
    font-size: 16px;
  }

  .playlist-name {
    font-size: 16px;
  }
}
</style>
