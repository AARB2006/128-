<!--
Name and description inputs shared by the add and edit forms.
-->
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
  <div class="fields flex flex-col">
    <label class="label mb-1.5 text-[14px] font-bold not-first:mt-4" :for="`${idPrefix}-name`">
      Name
    </label>
    <input
      :id="`${idPrefix}-name`"
      ref="nameInput"
      v-model="name"
      class="name-input font-inherit min-h-11 w-full rounded-[10px] border border-border bg-surface px-4 py-0 text-[16px] text-text disabled:cursor-not-allowed disabled:text-muted"
      type="text"
      autocomplete="off"
      placeholder="Playlist name"
      :maxlength="NAME_MAX + 50"
      :disabled="disabled"
    />
    <p
      v-if="name.trim().length > NAME_MAX"
      class="over-note mt-1.5 mb-0 text-[13px] text-danger"
      role="alert"
    >
      The name can be at most {{ NAME_MAX }} characters.
    </p>

    <label
      class="label mb-1.5 text-[14px] font-bold not-first:mt-4"
      :for="`${idPrefix}-description`"
    >
      Description <span class="optional font-normal text-muted">(optional)</span>
    </label>
    <div
      class="box relative rounded-card border border-border bg-surface focus-within:outline-3 focus-within:outline-offset-2 focus-within:outline-focus [&.over]:border-danger"
      :class="{ over: description.length > DESCRIPTION_MAX, disabled }"
    >
      <textarea
        :id="`${idPrefix}-description`"
        ref="descriptionInput"
        v-model="description"
        class="font-inherit block min-h-[140px] w-full resize-y rounded-card border-0 bg-transparent px-4 pt-3.5 pb-10 text-[16px] leading-[1.5] text-text outline-0 placeholder:text-muted disabled:cursor-not-allowed disabled:text-muted"
        placeholder="What is this playlist for?"
        :disabled="disabled"
      ></textarea>
      <span
        class="counter absolute right-4 bottom-2.5 text-[14px] text-muted tabular-nums [&.over]:font-bold [&.over]:text-danger"
        :class="{ over: description.length > DESCRIPTION_MAX }"
        aria-live="polite"
      >
        {{ description.length }}/{{ DESCRIPTION_MAX }}
      </span>
    </div>
  </div>
</template>
