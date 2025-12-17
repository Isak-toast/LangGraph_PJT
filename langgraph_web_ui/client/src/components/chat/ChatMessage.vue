<script setup lang="ts">
import { ref, computed } from 'vue';
import { SparklesIcon, UserIcon, BrainIcon, ChevronDownIcon } from 'lucide-vue-next';
import MarkdownIt from 'markdown-it';

// Props
interface Message {
  id: number;
  role: 'user' | 'ai';
  content: string;
  thoughts?: string[];
  activeNode?: string | null;
  timestamp: number;
}

const props = defineProps<{
  message: Message;
}>();

// Markdown renderer
const md = new MarkdownIt({
  html: false,
  linkify: true,
  typographer: true,
});

// State
const isThinkingOpen = ref(false);

// Computed
const isUser = computed(() => props.message.role === 'user');
const hasThoughts = computed(() => props.message.thoughts && props.message.thoughts.length > 0);

const renderedContent = computed(() => {
  return md.render(props.message.content || '');
});

const formatTime = (timestamp: number) => {
  return new Date(timestamp).toLocaleTimeString('ko-KR', {
    hour: '2-digit',
    minute: '2-digit',
  });
};
</script>

<template>
  <!-- ========== USER MESSAGE ========== -->
  <div v-if="isUser" class="gemini-user-message">
    <div class="gemini-user-bubble">
      {{ message.content }}
    </div>
  </div>

  <!-- ========== AI MESSAGE ========== -->
  <div v-else class="gemini-ai-message">
    <!-- Gemini Avatar (Gradient Sparkle) -->
    <div class="gemini-ai-avatar">
      <SparklesIcon class="w-4 h-4 text-white" />
    </div>
    
    <!-- AI Content -->
    <div class="flex-1 min-w-0">
      <!-- Thinking Process (Collapsible) -->
      <div 
        v-if="hasThoughts" 
        class="mb-4 rounded-xl overflow-hidden border border-[hsl(var(--gemini-border))] bg-[hsl(var(--gemini-bg-surface))]"
      >
        <button 
          @click="isThinkingOpen = !isThinkingOpen"
          class="w-full flex items-center gap-2 px-4 py-3 text-sm text-[hsl(var(--gemini-text-secondary))] hover:bg-[hsl(var(--gemini-bg-hover))] transition-colors"
        >
          <BrainIcon class="w-4 h-4 text-[hsl(var(--gemini-accent-blue))]" />
          <span>사고 과정 보기</span>
          <div class="flex-1"></div>
          <ChevronDownIcon 
            class="w-4 h-4 transition-transform duration-200" 
            :class="{ 'rotate-180': isThinkingOpen }"
          />
        </button>
        
        <div 
          v-show="isThinkingOpen" 
          class="px-4 py-3 border-t border-[hsl(var(--gemini-border))] space-y-2 bg-[hsl(var(--gemini-bg-primary))]"
        >
          <div 
            v-for="(thought, idx) in message.thoughts" 
            :key="idx"
            class="text-xs font-mono text-[hsl(var(--gemini-text-secondary))] pl-4 border-l-2 border-[hsl(var(--gemini-accent-blue))]"
          >
            {{ thought }}
          </div>
          <div 
            v-if="message.activeNode"
            class="flex items-center gap-2 text-xs text-[hsl(var(--gemini-accent-blue))]"
          >
            <span class="relative flex h-2 w-2">
              <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-[hsl(var(--gemini-accent-blue))] opacity-75"></span>
              <span class="relative inline-flex rounded-full h-2 w-2 bg-[hsl(var(--gemini-accent-blue))]"></span>
            </span>
            <span>현재 노드: {{ message.activeNode }}</span>
          </div>
        </div>
      </div>
      
      <!-- Main Content (NO BUBBLE - Clean Text) -->
      <div 
        class="gemini-ai-content prose prose-invert prose-sm max-w-none"
        v-html="renderedContent"
      ></div>
      
      <!-- Timestamp -->
      <div class="mt-2 text-xs text-[hsl(var(--gemini-text-disabled))]">
        {{ formatTime(message.timestamp) }}
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Prose overrides for Gemini style */
.prose :where(p):not(:where([class~="not-prose"] *)) {
  margin-top: 0.75em;
  margin-bottom: 0.75em;
}

.prose :where(code):not(:where([class~="not-prose"] *)) {
  background-color: hsl(var(--gemini-bg-elevated));
  padding: 0.2em 0.4em;
  border-radius: 4px;
  font-size: 0.875em;
}

.prose :where(pre):not(:where([class~="not-prose"] *)) {
  background-color: hsl(var(--gemini-bg-surface));
  border: 1px solid hsl(var(--gemini-border));
  border-radius: 12px;
  padding: 16px;
  overflow-x: auto;
}
</style>
