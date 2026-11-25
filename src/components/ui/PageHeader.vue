<!--
Page title with an optional description, and the page's main buttons on the right.
-->
<script setup>
defineProps({
  title: { type: String, default: '' },
  description: { type: String, default: '' },
})
</script>

<template>
  <header class="page-header mb-6 flex flex-wrap items-end justify-between gap-4">
    <div class="min-w-0">
      <!-- The `title` slot replaces the plain title (the playlist page's
           editable name uses it). -->
      <slot name="title">
        <h1 class="app-page-title m-0">{{ title }}</h1>
      </slot>
      <p v-if="description" class="mt-1 mb-0 text-[15px] text-muted">{{ description }}</p>
      <slot name="below" />
    </div>
    <div v-if="$slots.actions" class="actions flex flex-wrap items-center gap-2">
      <slot name="actions" />
    </div>
  </header>
</template>
