<script setup>
import { nextTick, onMounted, ref } from 'vue'
import { DESCRIPTION_MAX, NAME_MAX } from '@/services/playlistRules.js'

// The name and description inputs, shared by the Add Playlist page and the
// edit popup. The description box looks like the Import Music link box.
const name = defineModel('name', { type: String, default: '' })
const description = defineModel('description', { type: String, default: '' })

const props = defineProps({
  disabled: { type: Boolean, default: false },
  // Which field gets the cursor when this appears.
  focus: { type: String, default: 'name' },
  // Makes the ids unique when two copies could exist on one page.
  idPrefix: { type: String, default: 'playlist' },
})

const nameInput = ref(null)
const descriptionInput = ref(null)

onMounted(async () => {
  // Wait a tick so a popup has finished opening before the cursor goes in.
  await nextTick()
  const target = props.focus === 'description' ? descriptionInput : nameInput
  target.value?.focus()
  // Put the cursor after the existing text instead of selecting it.
  const length = target.value?.value.length ?? 0
  target.value?.setSelectionRange?.(length, length)
})
</script>

<template>
  <div class="fields">
    <label class="label" :for="`${idPrefix}-name`">Name</label>
    <input
      :id="`${idPrefix}-name`"
      ref="nameInput"
      v-model="name"
      class="name-input"
      type="text"
      autocomplete="off"
      placeholder="Playlist name"
      :maxlength="NAME_MAX + 50"
      :disabled="disabled"
    />
    <p v-if="name.trim().length > NAME_MAX" class="over-note" role="alert">
      The name can be at most {{ NAME_MAX }} characters.
    </p>

    <label class="label" :for="`${idPrefix}-description`">
      Description <span class="optional">(optional)</span>
    </label>
    <div class="box" :class="{ over: description.length > DESCRIPTION_MAX, disabled }">
      <textarea
        :id="`${idPrefix}-description`"
        ref="descriptionInput"
        v-model="description"
        placeholder="What is this playlist for?"
        :disabled="disabled"
      ></textarea>
      <span
        class="counter"
        :class="{ over: description.length > DESCRIPTION_MAX }"
        aria-live="polite"
      >
        {{ description.length }}/{{ DESCRIPTION_MAX }}
      </span>
    </div>
  </div>
</template>

<style scoped>
.fields {
  display: flex;
  flex-direction: column;
}

.label {
  margin: 0 0 6px;
  font-size: 14px;
  font-weight: bold;
}

.label:not(:first-child) {
  margin-top: 16px;
}

.optional {
  font-weight: normal;
  color: var(--c-muted);
}

.name-input {
  width: 100%;
  min-height: 44px;
  padding: 0 16px;
  border: 1px solid var(--c-border);
  border-radius: 10px;
  background: var(--c-surface);
  color: var(--c-text);
  font: inherit;
  font-size: 16px;
}

.name-input:disabled {
  color: var(--c-muted);
  cursor: not-allowed;
}

.over-note {
  margin: 6px 0 0;
  font-size: 13px;
  color: var(--c-danger);
}

.box {
  position: relative;
  border: 1px solid var(--c-border);
  border-radius: var(--radius);
  background: var(--c-surface);
}

.box:focus-within {
  outline: 3px solid #98a2b3;
  outline-offset: 2px;
}

.box.over {
  border-color: var(--c-danger);
}

textarea {
  display: block;
  width: 100%;
  min-height: 140px;
  padding: 14px 16px 40px;
  border: 0;
  border-radius: var(--radius);
  outline: 0;
  resize: vertical;
  background: transparent;
  color: var(--c-text);
  font: inherit;
  font-size: 16px;
  line-height: 1.5;
}

textarea::placeholder {
  color: var(--c-muted);
}

textarea:disabled {
  color: var(--c-muted);
  cursor: not-allowed;
}

.counter {
  position: absolute;
  right: 16px;
  bottom: 10px;
  font-size: 14px;
  font-variant-numeric: tabular-nums;
  color: var(--c-muted);
}

.counter.over {
  color: var(--c-danger);
  font-weight: bold;
}
</style>