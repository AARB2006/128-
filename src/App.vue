<!--
Root component: shows the current page and leaves
protected pages when the session ends.
-->
<script setup>
import { watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth.js'
import { useSignOut } from '@/composables/useSignOut.js'

// If the session ends (log out in another tab, or it expires),
// leave any protected page.
const router = useRouter()
const { isAuthenticated } = useAuth()
// Logging out from this tab shows "Logging you out…" and then reloads on
// the landing page itself, so don't cut that short here.
const { signingOut } = useSignOut()

watch(isAuthenticated, (signedIn) => {
  if (!signedIn && !signingOut.value && router.currentRoute.value.meta.requiresAuth) {
    router.replace({ name: 'landing' })
  }
})
</script>

<template>
  <RouterView />
</template>