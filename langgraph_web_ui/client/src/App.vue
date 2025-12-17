<script setup lang="ts">
import { ref, watch, nextTick, computed } from 'vue';
import { useChatStore } from './stores/chat';
import { storeToRefs } from 'pinia';
import ChatMessage from './components/chat/ChatMessage.vue';
import GraphCanvas from './components/GraphCanvas.vue';
import { SendIcon, MenuIcon, XIcon, PlusIcon, SettingsIcon, SparklesIcon } from 'lucide-vue-next';

// Store
const chatStore = useChatStore();
const { messages, isLoading } = storeToRefs(chatStore);

// Local state
const input = ref('');
const messagesEndRef = ref<HTMLElement | null>(null);
const isSidebarOpen = ref(true);

// Computed
const activeNode = computed(() => {
  if (messages.value.length === 0) return null;
  const lastMsg = messages.value[messages.value.length - 1];
  return lastMsg?.activeNode || null;
});

const hasInput = computed(() => input.value.trim().length > 0);

// Methods
const handleSend = async () => {
  if (!input.value.trim() || isLoading.value) return;
  const text = input.value;
  input.value = '';
  await chatStore.sendMessage(text);
};

const handleSuggestion = (topic: string) => {
  input.value = topic;
  handleSend();
};

const scrollToBottom = () => {
  nextTick(() => {
    messagesEndRef.value?.scrollIntoView({ behavior: 'smooth' });
  });
};

// Watchers
watch(() => messages.value.length, scrollToBottom);
watch(() => messages.value[messages.value.length - 1]?.content, scrollToBottom);

// Suggestion topics
const suggestions = [
  '2024년 AI 에이전트 트렌드 분석',
  'LangGraph의 핵심 패턴 설명',
  'FastAPI SSE 스트리밍 구현 방법'
];
</script>

<template>
  <div class="flex h-screen overflow-hidden">
    
    <!-- ========== SIDEBAR ========== -->
    <aside 
      class="gemini-sidebar fixed inset-y-0 left-0 z-30 flex flex-col transition-transform duration-300"
      :class="isSidebarOpen ? 'translate-x-0' : '-translate-x-full'"
    >
      <!-- Sidebar Header -->
      <div class="h-16 flex items-center px-4">
        <button 
          @click="isSidebarOpen = false"
          class="p-2 rounded-full hover:bg-[hsl(var(--gemini-bg-hover))] transition-colors"
        >
          <MenuIcon class="w-5 h-5" />
        </button>
      </div>
      
      <!-- New Chat Button -->
      <div class="px-3 mb-4">
        <button class="gemini-sidebar-item flex items-center gap-3 w-full bg-[hsl(var(--gemini-bg-hover))]">
          <PlusIcon class="w-5 h-5" />
          <span class="text-sm font-medium">새 채팅</span>
        </button>
      </div>
      
      <!-- Chat History (Placeholder) -->
      <div class="flex-1 overflow-y-auto px-2">
        <div class="text-xs text-[hsl(var(--gemini-text-secondary))] px-4 py-2">최근</div>
        <div class="gemini-sidebar-item text-sm truncate">AI 에이전트 연구</div>
        <div class="gemini-sidebar-item text-sm truncate">LangGraph 패턴 분석</div>
      </div>
      
      <!-- Graph Visualization (Hidden in Sidebar) -->
      <div class="h-48 mx-3 mb-3 rounded-xl overflow-hidden border border-[hsl(var(--gemini-border))] bg-[hsl(var(--gemini-bg-primary))]">
        <div class="text-xs text-[hsl(var(--gemini-text-secondary))] p-2">Live Graph</div>
        <GraphCanvas :activeNode="activeNode" />
      </div>
      
      <!-- Sidebar Footer -->
      <div class="p-4 border-t border-[hsl(var(--gemini-border))]">
        <button class="gemini-sidebar-item flex items-center gap-3 w-full">
          <SettingsIcon class="w-5 h-5" />
          <span class="text-sm">설정</span>
        </button>
      </div>
    </aside>

    <!-- ========== MAIN CONTENT ========== -->
    <div 
      class="flex-1 flex flex-col h-screen transition-all duration-300"
      :class="isSidebarOpen ? 'ml-[280px]' : 'ml-0'"
    >
      <!-- Header -->
      <header class="h-16 flex items-center justify-between px-6 flex-shrink-0">
        <div class="flex items-center gap-3">
          <button 
            v-if="!isSidebarOpen"
            @click="isSidebarOpen = true"
            class="p-2 rounded-full hover:bg-[hsl(var(--gemini-bg-hover))] transition-colors"
          >
            <MenuIcon class="w-5 h-5" />
          </button>
          <div class="flex items-center gap-2">
            <div class="gemini-ai-avatar w-8 h-8">
              <SparklesIcon class="w-4 h-4 text-white" />
            </div>
            <span class="font-medium text-lg">Gemini</span>
            <span class="text-xs text-[hsl(var(--gemini-text-secondary))] bg-[hsl(var(--gemini-bg-surface))] px-2 py-0.5 rounded">1.5 Flash</span>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <div class="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-500"></div>
        </div>
      </header>

      <!-- Chat Area -->
      <main class="flex-1 overflow-y-auto">
        <div class="max-w-[768px] mx-auto px-4 py-6 min-h-full flex flex-col">
          
          <!-- Welcome Screen (Empty State) -->
          <div 
            v-if="messages.length === 0" 
            class="gemini-welcome flex-1 animate-fade-in-up"
          >
            <h1 class="gemini-welcome-title">
              <span class="gemini-gradient-text">안녕하세요. 저는 Gemini입니다.</span>
            </h1>
            <p class="gemini-welcome-subtitle">
              무엇을 도와드릴까요?
            </p>
            
            <!-- Suggestion Chips -->
            <div class="gemini-suggestion-chips">
              <button 
                v-for="topic in suggestions" 
                :key="topic"
                @click="handleSuggestion(topic)"
                class="gemini-chip"
              >
                {{ topic }}
              </button>
            </div>
          </div>

          <!-- Messages -->
          <div v-else class="flex-1">
            <ChatMessage 
              v-for="msg in messages" 
              :key="msg.id" 
              :message="msg" 
            />
            <div ref="messagesEndRef" class="h-8"></div>
          </div>
        </div>
      </main>

      <!-- Fixed Bottom Input Area -->
      <div class="flex-shrink-0 p-4 pb-6">
        <div class="max-w-[768px] mx-auto">
          <form @submit.prevent="handleSend" class="gemini-input-container flex items-center">
            <input 
              v-model="input"
              type="text"
              class="gemini-input"
              placeholder="여기에 프롬프트를 입력하세요"
              :disabled="isLoading"
            />
            <button 
              type="submit"
              class="gemini-send-button"
              :class="{ 'active': hasInput && !isLoading }"
              :disabled="!hasInput || isLoading"
            >
              <SendIcon v-if="!isLoading" class="w-5 h-5" />
              <div v-else class="w-5 h-5 border-2 border-current border-t-transparent rounded-full animate-spin"></div>
            </button>
          </form>
          <p class="text-center text-xs text-[hsl(var(--gemini-text-secondary))] mt-3">
            Gemini는 실수를 할 수 있으므로 답변을 다시 확인해 보세요.
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
