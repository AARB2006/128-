<script setup>
import { computed } from 'vue'

// A rounded progress bar with moving stripes while work is running.
// Same look as the Import Music bar.
const props = defineProps({
  percent: { type: Number, default: 0 },
  active: { type: Boolean, default: false }, // work is running: animate the stripes
  indeterminate: { type: Boolean, default: false }, // no number yet: slide back and forth
  failed: { type: Boolean, default: false },
  label: { type: String, default: 'Progress' },
  small: { type: Boolean, default: false },
})

// Before anything has finished the bar would look empty, so give it a sliver.
const width = computed(() => (props.active ? Math.max(props.percent, 4) : props.percent))
</script>

<template>
  <div
    class="track"
    :class="{ small, failed }"
    role="progressbar"
    aria-valuemin="0"
    aria-valuemax="100"
    :aria-valuenow="indeterminate ? undefined : percent"
    :aria-label="label"
  >
    <div
      class="fill"
      :class="{ active, sliding: indeterminate }"
      :style="indeterminate ? undefined : { width: `${width}%` }"
    ></div>
  </div>
</template>

<style scoped>
.track {
  position: relative;
  height: 14px;
  overflow: hidden;
  border-radius: 999px;
  background: var(--c-hover);
  box-shadow: inset 0 0 0 1px var(--c-border);
}

.track.small {
  height: 8px;
}

.fill {
  position: absolute;
  inset: 0 auto 0 0;
  width: 0;
  border-radius: 999px;
  background-color: var(--c-accent);
  transition: width 500ms ease;
}

.failed .fill {
  background-color: var(--c-danger);
}

.fill.active {
  background-image: repeating-linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.22) 0 10px,
    transparent 10px 20px
  );
  background-size: 28px 28px;
  animation: stripes 0.9s linear infinite;
}

.fill.sliding {
  width: 35%;
  animation:
    stripes 0.9s linear infinite,
    slide 1.3s ease-in-out infinite;
  transition: none;
}

@keyframes stripes {
  to {
    background-position: 28px 0;
  }
}

@keyframes slide {
  0% {
    left: -35%;
  }

  100% {
    left: 100%;
  }
}

@media (prefers-reduced-motion: reduce) {
  .fill.active,
  .fill.sliding {
    animation: none;
  }

  .fill.sliding {
    width: 100%;
  }

  .fill {
    transition: none;
  }
}
</style>
