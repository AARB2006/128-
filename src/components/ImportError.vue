<script setup>
import { useLinks } from '../composables/useLinks.js'

const { error } = useLinks()
</script>

<template>
  <div v-if="error" class="import-error" role="alert">
    <p class="message">{{ error.message }}</p>

    <ul v-if="error.problems.length" class="problems">
      <li v-for="problem in error.problems" :key="problem.line">
        Line {{ problem.line }}: {{ problem.reason }}
        <code>{{ problem.url }}</code>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.import-error {
  margin: 0 0 10px;
  padding: 10px 13px;
  border: 1px solid #e2a19b;
  background: #fff5f4;
  color: #8f1d16;
  font-size: 14px;
  line-height: 1.45;
}

.message {
  margin: 0;
}

.problems {
  margin: 6px 0 0;
  padding-left: 20px;
}

code {
  overflow-wrap: anywhere;
  font-size: 13px;
}
</style>
