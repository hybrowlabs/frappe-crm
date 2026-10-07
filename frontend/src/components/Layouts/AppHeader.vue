<template>
  <div class="relative flex border-b pr-5">
    <div id="app-header" class="flex-1"></div>
    <!-- Brand wordmark, centred over the whole header; clicks pass through to the page header below it. -->
    <div class="pointer-events-none absolute inset-0 hidden items-center justify-center lg:flex">
      <span class="whitespace-nowrap text-[18px] font-bold tracking-[-0.01em] text-[#0060AA]">
        ॐ Precious Alloys ॐ
      </span>
    </div>
    <div class="flex items-center justify-center">
      <CallUI />
    </div>
  </div>
</template>

<script setup>
import CallUI from '@/components/Telephony/CallUI.vue'
</script>
