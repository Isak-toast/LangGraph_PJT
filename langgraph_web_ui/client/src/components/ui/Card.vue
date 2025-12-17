<template>
  <div :class="['rounded-xl border bg-card text-card-foreground shadow', className]">
    <div class="p-6 pt-0" v-if="$slots.header">
       <slot name="header"></slot>
    </div>
    <div class="p-6 pt-0">
      <slot></slot>
    </div>
    <div class="flex items-center p-6 pt-0" v-if="$slots.footer">
      <slot name="footer"></slot>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  className?: string
}>()
</script>
