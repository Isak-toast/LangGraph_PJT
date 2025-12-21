<script setup lang="ts">
import { ref, computed } from 'vue';
import { NetworkIcon, BrainIcon, ChevronDownIcon } from 'lucide-vue-next';
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
    <!-- AI Avatar -->
    <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center flex-shrink-0 shadow-lg shadow-violet-500/20">
      <NetworkIcon class="w-5 h-5 text-white" />
    </div>
    
    <!-- AI Content -->
    <div class="flex-1 min-w-0">
      <!-- Thinking Process (Collapsible) -->
      <div 
        v-if="hasThoughts" 
        class="mb-4 rounded-2xl overflow-hidden border border-gray-200 bg-gray-50/50"
      >
        <button 
          @click="isThinkingOpen = !isThinkingOpen"
          class="w-full flex items-center gap-3 px-4 py-3 text-sm text-gray-600 hover:bg-gray-100 transition-colors"
        >
          <div class="w-7 h-7 rounded-lg bg-violet-100 flex items-center justify-center">
            <BrainIcon class="w-4 h-4 text-violet-600" />
          </div>
          <span class="font-medium">사고 과정 보기</span>
          <span class="text-xs text-gray-400">({{ message.thoughts?.length }}단계)</span>
          <div class="flex-1"></div>
          <ChevronDownIcon 
            class="w-5 h-5 text-gray-400 transition-transform duration-200" 
            :class="{ 'rotate-180': isThinkingOpen }"
          />
        </button>
        
        <div 
          v-show="isThinkingOpen" 
          class="px-4 py-3 border-t border-gray-200 space-y-2 bg-white"
        >
          <div 
            v-for="(thought, idx) in message.thoughts" 
            :key="idx"
            class="flex items-start gap-3 text-sm text-gray-600 p-2 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <div class="w-5 h-5 rounded-full bg-violet-100 flex items-center justify-center flex-shrink-0 mt-0.5">
              <span class="text-xs font-medium text-violet-600">{{ idx + 1 }}</span>
            </div>
            <span class="leading-relaxed">{{ thought }}</span>
          </div>
          <div 
            v-if="message.activeNode"
            class="flex items-center gap-2 text-sm text-violet-600 bg-violet-50 p-3 rounded-xl"
          >
            <span class="relative flex h-2 w-2">
              <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-violet-500 opacity-75"></span>
              <span class="relative inline-flex rounded-full h-2 w-2 bg-violet-500"></span>
            </span>
            <span class="font-medium">현재 실행 중: {{ message.activeNode }}</span>
          </div>
        </div>
      </div>
      
      <!-- Main Content -->
      <div 
        class="gemini-ai-content prose prose-gray prose-sm max-w-none"
        v-html="renderedContent"
      ></div>
      
      <!-- Timestamp -->
      <div class="mt-3 text-xs text-gray-400">
        {{ formatTime(message.timestamp) }}
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Prose overrides for light theme */
.prose :where(p):not(:where([class~="not-prose"] *)) {
  margin-top: 0.75em;
  margin-bottom: 0.75em;
}

.prose :where(code):not(:where([class~="not-prose"] *)) {
  background-color: #f4f4f5;
  color: #7c3aed;
  padding: 0.2em 0.5em;
  border-radius: 6px;
  font-size: 0.875em;
  font-weight: 500;
}

.prose :where(pre):not(:where([class~="not-prose"] *)) {
  background-color: #fafafa;
  border: 1px solid #e5e5e5;
  border-radius: 12px;
  padding: 16px;
  overflow-x: auto;
}

.prose :where(a):not(:where([class~="not-prose"] *)) {
  color: #7c3aed;
  text-decoration: none;
}

.prose :where(a):not(:where([class~="not-prose"] *)):hover {
  text-decoration: underline;
}
</style>
