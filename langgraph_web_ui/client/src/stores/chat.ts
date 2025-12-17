import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { streamChat } from '../services/api'

export interface Message {
    id: number;
    role: 'user' | 'ai';
    content: string;
    timestamp: number;
}

export interface NodeStatus {
    name: string;
    status: 'idle' | 'running' | 'done';
}

export const useChatStore = defineStore('chat', () => {
    const messages = ref<Message[]>([]);
    const isLoading = ref(false);
    const threadId = ref(`thread_${Date.now()}`);
    const activeNode = ref<string | null>(null);

    // Helper to add message
    const addMessage = (role: 'user' | 'ai', content: string) => {
        messages.value.push({
            id: Date.now(),
            role,
            content,
            timestamp: Date.now(),
        });
    };

    const sendMessage = async (text: string) => {
        if (!text.trim()) return;

        addMessage('user', text);
        isLoading.value = true;

        // Create placeholder for AI response
        const aiMsgId = Date.now() + 1;
        messages.value.push({
            id: aiMsgId,
            role: 'ai',
            content: "", // streaming buffer
            timestamp: Date.now(),
        });

        const aiMsgIndex = messages.value.findIndex(m => m.id === aiMsgId);

        await streamChat(
            { message: text, thread_id: threadId.value },
            (event) => {
                if (event.type === 'token') {
                    messages.value[aiMsgIndex].content += event.content;
                } else if (event.type === 'node_start') {
                    activeNode.value = event.node;
                } else if (event.type === 'node_end') {
                    activeNode.value = null;
                }
            },
            (err) => {
                console.error("Stream error", err);
                isLoading.value = false;
                activeNode.value = null;
                addMessage('ai', `Error: ${err}`);
            },
            () => {
                isLoading.value = false;
                activeNode.value = null;
            }
        );
    };

    return {
        messages,
        isLoading,
        threadId,
        activeNode,
        sendMessage
    }
})
