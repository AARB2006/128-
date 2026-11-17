<script setup>
import { computed } from 'vue'

const props = defineProps({
  phase: { type: String, default: 'idle' }, // idle | starting | running | finished
  label: { type: String, default: '' },
  percent: { type: Number, default: 0 },
  failed: { type: Boolean, default: false },
})

const active = computed(() => props.phase === 'starting' || props.phase === 'running')

// Before the first link finishes the bar would be empty, so give it a sliver.
const width = computed(() => (active.value ? Math.max(props.percent, 4) : props.percent))
</script>

<template>
  <div class="progress" :class="{ failed }" role="status" aria-live="polite">
    <p class="label">{{ label }}</p>

    <div
      class="track"
      role="progressbar"
      aria-valuemin="0"
      aria-valuemax="100"
      :aria-valuenow="phase === 'starting' ? undefined : percent"
      :aria-label="label"
    >
      <div
        class="fill"
        :class="{ active, sliding: phase === 'starting' }"
        :style="phase === 'starting' ? undefined : { width: `${width}%` }"
      ></div>
    </div>
  </div>
</template>

<style scoped>
.progress {
  padding: 16px 18px;
  border: 1px solid var(--c-border);
  border-radius: var(--radius);
  background: var(--c-surface);
}

.label {
  margin: 0 0 10px;
  font-size: 16px;
  font-weight: bold;
  font-variant-numeric: tabular-nums;
}

.track {
  position: relative;
  height: 14px;
  overflow: hidden;
  border-radius: 999px; /* fully rounded, like the buttons and cards */
  background: var(--c-hover);
  box-shadow: inset 0 0 0 1px var(--c-border);
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

/* While work is running: light stripes drifting across the dark bar. */
.fill.active {
  background-image: repeating-linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.22) 0 10px,
    transparent 10px 20px
  );
  background-size: 28px 28px;
  animation: stripes 0.9s linear infinite;
}

/* Before the first progress arrives: a bar sliding back and forth. */
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