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
  <!-- The landing page sits outside .app-shell, so it uses its own literal
       colours rather than the --c-* tokens. -->
  <main class="landing flex min-h-screen items-center justify-center px-6 py-12">
    <section
      class="card flex w-[min(100%,560px)] flex-col items-center gap-6 border-3 border-[#111] px-8 py-12 text-center phone:px-5 phone:py-8"
      aria-labelledby="title"
    >
      <h1 id="title" class="m-0 text-[32px] leading-[1.2] phone:text-[26px]">
        YT-MP3: Family Playlist Maker
      </h1>
      <p class="tagline m-0 text-[18px] text-[#444]">
        Keep your family's music in one place and build playlists for offline
        listening.
      </p>

      <!-- Same look as the POC's shared .action-button (style.css), but full
           width on phones instead of half. -->
      <button
        class="font-inherit min-h-16 w-[230px] min-w-[170px] cursor-pointer rounded-none border-3 border-[#111] bg-[#fff] px-6 py-2.5 text-[20px] text-[#111] transition-[background,color] duration-[120ms] ease-[ease] focus-visible:outline-3 focus-visible:outline-offset-3 focus-visible:outline-[#777] enabled:hover:bg-[#111] enabled:hover:text-[#fff] disabled:cursor-not-allowed disabled:border-[#999] disabled:bg-[#f2f2f2] disabled:text-[#777] phone:min-h-[54px] phone:w-full phone:min-w-0 phone:px-3 phone:py-2 phone:text-[16px]"
        type="button"
        :disabled="busy"
        @click="onContinue"
      >
        {{ busy ? 'Redirecting…' : 'Continue with Google' }}
      </button>

      <p v-if="error" class="error m-0 text-[#b00020]" role="alert">{{ error }}</p>
    </section>
  </main>
</template>
