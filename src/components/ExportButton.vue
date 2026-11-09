<template>
  <button class="export-button" type="button">
    export
  </button>
</template>

<style scoped>
.export-button {
  width: 230px;
  min-width: 170px;
  min-height: 64px;
  padding: 10px 24px;
  border: 3px solid #111;
  border-radius: 0;
  background: #fff;
  color: #111;
  cursor: pointer;
  font: inherit;
  font-size: 20px;
  transition: background 120ms ease, color 120ms ease;
}

.export-button:hover {
  background: #111;
  color: #fff;
}

.export-button:focus-visible {
  outline: 3px solid #777;
  outline-offset: 3px;
}

@media (max-width: 640px) {
  .export-button {
    width: 50%;
    min-width: 0;
    min-height: 54px;
    padding: 8px 12px;
    font-size: 16px;
  }
}
</style>
