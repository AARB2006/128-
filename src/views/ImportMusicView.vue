<script setup>
import PlaceholderPage from '@/components/layout/PlaceholderPage.vue'
</script>

<template>
  <PlaceholderPage
    title="Import Music"
    description="Importing songs from YouTube links is coming in the next update."
  >
    <RouterLink :to="{ name: 'library' }" class="app-btn">
      Back to Music Library
    </RouterLink>
  </PlaceholderPage>
</template>