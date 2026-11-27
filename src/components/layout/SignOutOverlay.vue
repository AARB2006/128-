<!--
Full-screen "Logging you out…" while signing out, and the error if it fails.
-->
<script setup>
import { useSignOut } from '@/composables/useSignOut.js'

const { signingOut, error, clearError } = useSignOut()
</script>

<template>
  <Transition
    enter-active-class="transition-opacity duration-200 ease-out motion-reduce:transition-none"
    enter-from-class="opacity-0"
    leave-active-class="transition-opacity duration-150 ease-in motion-reduce:transition-none"
    leave-to-class="opacity-0"
  >
    <div
      v-if="signingOut"
      class="sign-out-overlay fixed inset-0 z-[70] flex flex-col items-center justify-center gap-4 bg-bg/90 backdrop-blur-sm"
      role="status"
      aria-live="assertive"
    >
      <span
        class="size-9 rounded-full border-3 border-border border-t-accent animate-spin motion-reduce:animate-none"
        aria-hidden="true"
      ></span>
      <p class="m-0 text-[16px] font-medium">Logging you out…</p>
    </div>
  </Transition>

  <div
    v-if="error"
    class="sign-out-error app-alert fixed bottom-6 left-1/2 z-[70] m-0 w-[min(92vw,460px)] -translate-x-1/2 justify-between shadow-[0_12px_32px_rgba(0,0,0,0.5)]"
    role="alert"
  >
    <span>{{ error }}</span>
    <button class="app-btn min-h-9" type="button" @click="clearError">Dismiss</button>
  </div>
</template>
