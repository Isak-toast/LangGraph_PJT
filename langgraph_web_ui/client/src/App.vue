<script setup lang="ts">
import { ref } from 'vue';
import { useChatStore } from '@/stores/chat';
import { storeToRefs } from 'pinia';
import ChatBubble from '@/components/ChatBubble.vue';
import GraphCanvas from '@/components/GraphCanvas.vue';

const chatStore = useChatStore();
const { messages, isLoading, activeNode } = storeToRefs(chatStore);
const input = ref("");

const handleSubmit = () => {
    if (!input.value.trim() || isLoading.value) return;
    chatStore.sendMessage(input.value);
    input.value = "";
};

</script>

<template>
  <div class="flex h-screen w-screen bg-background text-foreground overflow-hidden">
    
    <!-- Left: Graph Visualization & Status -->
    <div class="w-1/3 border-r p-4 flex flex-col gap-4 bg-muted/10">
      <h2 class="text-xl font-bold tracking-tight">Agentic Insight</h2>
      <div class="flex-1 min-h-0">
         <GraphCanvas :active-node="activeNode" />
      </div>
      <div class="h-1/3 border rounded-lg p-4 bg-card">
        <h3 class="font-semibold mb-2">System Log</h3>
        <div class="text-xs text-muted-foreground space-y-1 font-mono">
            <div v-if="activeNode">Running: <span class="text-primary font-bold">{{ activeNode }}</span></div>
            <div v-else>Status: <span class="text-green-500">Idle</span></div>
        </div>
      </div>
    </div>

    <!-- Right: Chat Interface -->
    <div class="flex-1 flex flex-col">
        <!-- Messages Area -->
        <div class="flex-1 overflow-y-auto p-6 space-y-4">
            <template v-if="messages.length === 0">
                <div class="h-full flex flex-col items-center justify-center text-muted-foreground opacity-50">
                    <p class="text-lg font-medium">Ask me to research something.</p>
                </div>
            </template>
            <ChatBubble 
                v-for="msg in messages" 
                :key="msg.id" 
                :role="msg.role" 
                :content="msg.content" 
            />
             <div v-if="isLoading && messages[messages.length-1].role !== 'ai'" class="text-sm text-muted-foreground animate-pulse">
                Thinking...
            </div>
        </div>

        <!-- Input Area -->
        <div class="p-4 border-t bg-background">
            <form @submit.prevent="handleSubmit" class="flex gap-2">
                <input 
                    v-model="input"
                    type="text" 
                    placeholder="Example: Research the future of AI agents..." 
                    class="flex-1 min-w-0 rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
                    :disabled="isLoading"
                />
                <button 
                    type="submit"
                    class="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground shadow hover:bg-primary/90 h-9 px-4 py-2"
                    :disabled="isLoading"
                >
                    Send
                </button>
            </form>
        </div>
    </div>
  </div>
</template>
