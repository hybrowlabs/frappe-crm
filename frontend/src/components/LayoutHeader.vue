<template>
  <Teleport v-if="showHeader" to="#app-header">
    <slot>
      <header
        class="flex h-[52px] items-center justify-between gap-2 py-[7px] sm:pl-5 pl-2"
      >
        <div class="flex min-w-0 items-center gap-2 overflow-hidden">
          <slot name="left-header" />
        </div>
        <div class="flex shrink-0 items-center gap-2">
          <slot name="right-header" class="flex items-center gap-2" />
        </div>
      </header>
    </slot>
  </Teleport>
</template>
<script setup>
import { ref, nextTick } from 'vue'

const showHeader = ref(false)

nextTick(() => {
  showHeader.value = true
})
</script>
