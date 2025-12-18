<script setup lang="ts">
import { ref, watch, nextTick, computed } from 'vue';
import { useChatStore } from './stores/chat';
import { storeToRefs } from 'pinia';
import ChatMessage from './components/chat/ChatMessage.vue';
import { 
  SendIcon, 
  MenuIcon, 
  PlusIcon, 
  SettingsIcon, 
  TrashIcon,
  NetworkIcon,
  MessageSquareIcon,
  SparklesIcon,
  XIcon
} from 'lucide-vue-next';

// Store
const chatStore = useChatStore();
const { messages, isLoading, sessions, currentSessionId } = storeToRefs(chatStore);

// Local state
const input = ref('');
const messagesEndRef = ref<HTMLElement | null>(null);
const isSidebarOpen = ref(true);

// Computed
const hasInput = computed(() => input.value.trim().length > 0);

// Format date for session list
const formatDate = (timestamp: number) => {
  const date = new Date(timestamp);
  const now = new Date();
  const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
  
  if (diffDays === 0) return '오늘';
  if (diffDays === 1) return '어제';
  if (diffDays < 7) return `${diffDays}일 전`;
  return date.toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' });
};

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

const handleNewChat = () => {
  chatStore.createNewSession();
};

const handleSwitchSession = (sessionId: string) => {
  chatStore.switchSession(sessionId);
};

const handleDeleteSession = (sessionId: string, event: Event) => {
  event.stopPropagation();
  chatStore.deleteSession(sessionId);
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
  'FastAPI SSE 스트리밍 구현'
];
</script>

<template>
  <div class="flex h-screen overflow-hidden bg-white">
    
    <!-- ========== SIDEBAR ========== -->
    <aside 
      class="sidebar-container fixed inset-y-0 left-0 z-30 flex flex-col w-72 transition-transform duration-300 ease-out"
      :class="isSidebarOpen ? 'translate-x-0' : '-translate-x-full'"
    >
      <!-- Sidebar Header -->
      <div class="h-16 flex items-center justify-between px-4">
        <div class="flex items-center gap-3">
          <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center shadow-lg shadow-violet-500/20">
            <SparklesIcon class="w-5 h-5 text-white" />
          </div>
          <span class="font-semibold text-gray-800 text-lg">Agentic Insight</span>
        </div>
        <button 
          @click="isSidebarOpen = false"
          class="p-2 rounded-xl hover:bg-gray-100 transition-colors lg:hidden"
        >
          <XIcon class="w-5 h-5 text-gray-500" />
        </button>
      </div>
      
      <!-- New Chat Button -->
      <div class="px-4 pb-4">
        <button 
          @click="handleNewChat"
          class="btn-primary w-full flex items-center justify-center gap-2"
        >
          <PlusIcon class="w-5 h-5" />
          <span>새 채팅</span>
        </button>
      </div>
      
      <!-- Session List -->
      <div class="flex-1 overflow-y-auto px-3">
        <div class="text-xs font-medium text-gray-400 uppercase tracking-wider px-3 py-2">
          최근 채팅
        </div>
        
        <div class="space-y-1">
          <button
            v-for="session in sessions"
            :key="session.id"
            @click="handleSwitchSession(session.id)"
            class="sidebar-item w-full flex items-center gap-3 text-left group"
            :class="{ 'active': session.id === currentSessionId }"
          >
            <MessageSquareIcon class="w-4 h-4 flex-shrink-0" />
            <div class="flex-1 min-w-0">
              <div class="text-sm truncate font-medium">{{ session.title }}</div>
              <div class="text-xs text-gray-400">{{ formatDate(session.updatedAt) }}</div>
            </div>
            <button
              @click.stop="(e) => handleDeleteSession(session.id, e)"
              class="opacity-0 group-hover:opacity-100 p-1.5 rounded-lg hover:bg-red-50 hover:text-red-500 transition-all"
            >
              <TrashIcon class="w-4 h-4" />
            </button>
          </button>
        </div>
        
        <div 
          v-if="sessions.length === 0" 
          class="px-4 py-12 text-center"
        >
          <div class="w-14 h-14 mx-auto mb-4 rounded-2xl bg-gray-100 flex items-center justify-center">
            <MessageSquareIcon class="w-7 h-7 text-gray-400" />
          </div>
          <p class="text-sm text-gray-500">
            아직 대화가 없습니다.<br/>
            새 채팅을 시작해보세요!
          </p>
        </div>
      </div>
      
      <!-- Sidebar Footer -->
      <div class="p-4 border-t border-gray-100">
        <button class="btn-ghost w-full flex items-center gap-3">
          <SettingsIcon class="w-5 h-5" />
          <span class="text-sm">설정</span>
        </button>
      </div>
    </aside>

    <!-- ========== MAIN CONTENT ========== -->
    <div 
      class="flex-1 flex flex-col h-screen transition-all duration-300"
      :class="isSidebarOpen ? 'lg:ml-72' : 'ml-0'"
    >
      <!-- Header -->
      <header class="h-16 flex items-center justify-between px-6 flex-shrink-0 bg-white/80 backdrop-blur-sm border-b border-gray-100">
        <div class="flex items-center gap-4">
          <button 
            v-if="!isSidebarOpen"
            @click="isSidebarOpen = true"
            class="p-2 rounded-xl hover:bg-gray-100 transition-colors"
          >
            <MenuIcon class="w-5 h-5 text-gray-600" />
          </button>
          <div class="flex items-center gap-3">
            <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center shadow-md">
              <NetworkIcon class="w-5 h-5 text-white" />
            </div>
            <div>
              <span class="font-semibold text-gray-800 text-lg">Agentic Insight</span>
              <span class="ml-2 text-xs text-violet-600 bg-violet-50 px-2 py-0.5 rounded-full font-medium">Multi-Agent</span>
            </div>
          </div>
        </div>
        <div class="flex items-center gap-3">
          <div class="w-9 h-9 rounded-full bg-gradient-to-br from-blue-400 to-violet-500 ring-2 ring-white shadow-md"></div>
        </div>
      </header>

      <!-- Chat Area -->
      <main class="flex-1 overflow-y-auto bg-gradient-to-b from-gray-50/30 to-white">
        <div class="max-w-3xl mx-auto px-4 py-8 min-h-full flex flex-col">
          
          <!-- Welcome Screen (Empty State) -->
          <div 
            v-if="messages.length === 0" 
            class="gemini-welcome flex-1"
          >
            <div class="w-20 h-20 mx-auto mb-8 rounded-3xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center shadow-xl shadow-violet-500/25">
              <SparklesIcon class="w-10 h-10 text-white" />
            </div>
            <h1 class="text-4xl font-normal text-gray-800 mb-3">
              안녕하세요.
            </h1>
            <h2 class="text-2xl font-normal text-gray-500 mb-2">
              <span class="gemini-gradient-text">Agentic Insight</span>입니다.
            </h2>
            <p class="text-gray-400 mb-10 max-w-md leading-relaxed">
              AI 에이전트 팀이 협력하여 질문에 답변합니다.<br/>
              Supervisor, Researcher, Writer가 함께 작업합니다.
            </p>
            
            <!-- Suggestion Chips -->
            <div class="flex flex-wrap gap-3 justify-center">
              <button 
                v-for="topic in suggestions" 
                :key="topic"
                @click="handleSuggestion(topic)"
                class="suggestion-chip"
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
      <div class="flex-shrink-0 p-4 pb-6 bg-gradient-to-t from-white via-white to-transparent">
        <div class="max-w-3xl mx-auto">
          <form @submit.prevent="handleSend" class="chat-input-container flex items-center">
            <input 
              v-model="input"
              type="text"
              class="chat-input"
              placeholder="여기에 프롬프트를 입력하세요"
              :disabled="isLoading"
            />
            <button 
              type="submit"
              class="absolute right-3 w-11 h-11 rounded-xl flex items-center justify-center transition-all"
              :class="hasInput && !isLoading 
                ? 'bg-gradient-to-r from-violet-500 to-purple-500 text-white shadow-md hover:shadow-lg' 
                : 'bg-gray-100 text-gray-400'"
              :disabled="!hasInput || isLoading"
            >
              <SendIcon v-if="!isLoading" class="w-5 h-5" />
              <div v-else class="w-5 h-5 border-2 border-current border-t-transparent rounded-full animate-spin"></div>
            </button>
          </form>
          <p class="text-center text-xs text-gray-400 mt-4">
            AI 에이전트들이 협력하여 답변을 생성합니다. 결과를 검토해 주세요.
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
