<!--
Progress bar shown while links are being imported.
-->
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

// The bar's look in each phase. The animations (import-stripes, import-slide)
// are defined in app.css. Picked here rather than with competing classes, so
// only one width, transition and animation ever applies. Class names must be
// written out in full (not built from pieces) so Tailwind can find them.
const fillClass = computed(() => {
  const sliding = props.phase === 'starting'
  return [
    active.value &&
      'bg-[image:repeating-linear-gradient(135deg,rgba(255,255,255,0.22)_0_10px,transparent_10px_20px)] bg-[length:28px_28px] motion-reduce:animate-none',
    sliding
      ? // Before the first progress arrives: a bar sliding back and forth.
        'w-[35%] transition-none animate-[import-stripes_0.9s_linear_infinite,import-slide_1.3s_ease-in-out_infinite] motion-reduce:w-full'
      : 'w-0 transition-[width] duration-500 ease-[ease] motion-reduce:transition-none',
    // While work is running: light stripes drifting across the dark bar.
    active.value && !sliding && 'animate-[import-stripes_0.9s_linear_infinite]',
  ]
})
</script>

<template>
  <div
    class="progress group rounded-card border border-border bg-surface px-4.5 py-4"
    :class="{ failed }"
    role="status"
    aria-live="polite"
  >
    <p class="label mt-0 mb-2.5 text-[16px] font-bold tabular-nums">{{ label }}</p>

    <div
      class="track relative h-3.5 overflow-hidden rounded-full bg-hover shadow-[inset_0_0_0_1px_var(--c-border)]"
      role="progressbar"
      aria-valuemin="0"
      aria-valuemax="100"
      :aria-valuenow="phase === 'starting' ? undefined : percent"
      :aria-label="label"
    >
      <div
        class="fill absolute inset-y-0 left-0 rounded-full bg-accent group-[.failed]:bg-danger"
        :class="[{ active, sliding: phase === 'starting' }, fillClass]"
        :style="phase === 'starting' ? undefined : { width: `${width}%` }"
      ></div>
    </div>
  </div>
</template>
