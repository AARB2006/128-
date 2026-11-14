<script setup>
import { ref } from 'vue'
import { useAuth } from '@/composables/useAuth.js'

const { signInWithGoogle } = useAuth()
const busy = ref(false)
const error = ref('')

async function onContinue() {
  busy.value = true
  error.value = ''
  try {
    // On success the browser leaves for Google, so there is nothing to do after.
    await signInWithGoogle()
  } catch (e) {
    error.value = e.message || 'Could not start Google sign-in.'
    busy.value = false
  }
}
</script>

<template>
  <main class="landing">
    <section class="card" aria-labelledby="title">
      <h1 id="title">YT-MP3: Family Playlist Maker</h1>
      <p class="tagline">
        Keep your family's music in one place and build playlists for offline
        listening.
      </p>

      <button
        class="action-button"
        type="button"
        :disabled="busy"
        @click="onContinue"
      >
        {{ busy ? 'Redirecting…' : 'Continue with Google' }}
      </button>

      <p v-if="error" class="error" role="alert">{{ error }}</p>
    </section>
  </main>
</template>

<style scoped>
.landing {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
}

.card {
  width: min(100%, 560px);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
  padding: 48px 32px;
  border: 3px solid #111;
  text-align: center;
}

h1 {
  margin: 0;
  font-size: 32px;
  line-height: 1.2;
}

.tagline {
  margin: 0;
  font-size: 18px;
  color: #444;
}

.error {
  margin: 0;
  color: #b00020;
}

@media (max-width: 640px) {
  .card {
    padding: 32px 20px;
  }

  h1 {
    font-size: 26px;
  }

  /* the shared button shrinks to half width on phones; keep this one full */
  .card :deep(.action-button) {
    width: 100%;
  }
}
</style>