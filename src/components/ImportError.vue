<template>
  <div class="import-error" role="alert" hidden>
    Error message will appear here.
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

.import-error[hidden] {
  display: none !important;
}
</style>
