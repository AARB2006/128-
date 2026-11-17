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
      <p class="app-muted">{{ description }}</p>
      <slot />
    </div>
  </section>
</template>

<style scoped>
p {
  margin: 0 0 16px;
}

p:last-child {
  margin-bottom: 0;
}
</style>