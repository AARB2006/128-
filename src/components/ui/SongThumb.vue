<!--
A song's YouTube thumbnail, or a music-note tile if there isn't one.
-->
<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  videoId: { type: String, default: '' },
})

// YouTube's public thumbnail for a video ID (320 x 180). IDs are 11 characters
// of letters, digits, - and _; anything else gets the placeholder.
const src = computed(() =>
  /^[\w-]{11}$/.test(props.videoId ?? '')
    ? `https://i.ytimg.com/vi/${props.videoId}/mqdefault.jpg`
    : null,
)

const failed = ref(false)
watch(src, () => (failed.value = false))
</script>

<template>
  <img
    v-if="src && !failed"
    class="thumb block h-10 w-[72px] shrink-0 rounded-[6px] bg-hover object-cover"
    :src="src"
    alt=""
    loading="lazy"
    referrerpolicy="no-referrer"
    @error="failed = true"
  />
  <span
    v-else
    class="thumb inline-flex h-10 w-[72px] shrink-0 items-center justify-center rounded-[6px] bg-hover text-muted"
    aria-hidden="true"
  >
    <svg
      class="size-4"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="2"
      stroke-linecap="round"
      stroke-linejoin="round"
    >
      <path d="M9 18V5l12-2v13" />
      <circle cx="6" cy="18" r="3" />
      <circle cx="18" cy="16" r="3" />
    </svg>
  </span>
</template>
