<!--
Simple coming-soon page with a title.
-->
<script setup>
defineProps({
  title: { type: String, required: true },
  description: { type: String, required: true },
})
</script>

<template>
  <section class="app-page">
    <h1 class="app-page-title">{{ title }}</h1>
    <div class="app-card">
      <p class="app-muted mt-0 mb-4 last:mb-0">{{ description }}</p>
      <slot />
    </div>
  </section>
</template>