<script setup>
import { watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth.js'

// If the session ends (log out here or in another tab, or it expires),
// leave any protected page.
const router = useRouter()
const { isAuthenticated } = useAuth()

watch(isAuthenticated, (signedIn) => {
  if (!signedIn && router.currentRoute.value.meta.requiresAuth) {
    router.replace({ name: 'landing' })
  }
})
</script>

<template>
  <RouterView />
</template>