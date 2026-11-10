<script setup>
import { useLinks } from '../composables/useLinks.js'

const { playlistName, busy } = useLinks()
</script>

<template>
  <section class="playlist-name-input" aria-label="Playlist name input">
    <label class="visually-hidden" for="playlist-name">Playlist name</label>

    <input
      id="playlist-name"
      v-model="playlistName"
      :disabled="busy"
      type="text"
      placeholder="enter playlist name..."
      maxlength="150"
    />
  </section>
</template>

<style scoped>
.playlist-name-input {
  width: 100%;
  height: 72px;
  margin-bottom: 16px;
  border: 3px solid #111;
  background: #fff;
}

input {
  display: block;
  width: 100%;
  height: 100%;
  padding: 12px 18px;
  border: 0;
  outline: 0;
  color: #111;
  background: transparent;
  font: inherit;
  font-size: 21px;
}

input:disabled {
  color: #777;
}

input::placeholder {
  color: #525151;
  opacity: 1;
}

.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

@media (max-width: 640px) {
  .playlist-name-input {
    height: 60px;
    margin-bottom: 12px;
  }

  input {
    padding: 10px 13px;
    font-size: 17px;
  }
}
</style>