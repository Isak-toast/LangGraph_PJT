<script setup lang="ts">
import { computed } from 'vue';
import MarkdownIt from 'markdown-it';
import { cn } from '@/lib/utils';

const props = defineProps<{
  content: string;
  role: 'user' | 'ai';
}>();

const md = new MarkdownIt();
const rendered = computed(() => md.render(props.content));

</script>

<template>
  <div :class="cn(
    'p-4 rounded-lg max-w-[80%] mb-4',
    role === 'user' ? 'bg-primary text-primary-foreground ml-auto' : 'bg-muted text-foreground'
  )">
    <div class="prose dark:prose-invert text-sm" v-html="rendered"></div>
  </div>
</template>

<style scoped>
/* Basic Markdown Styles if prose plugin not available */
:deep(p) { margin-bottom: 0.5em; }
:deep(p:last-child) { margin-bottom: 0; }
</style>
