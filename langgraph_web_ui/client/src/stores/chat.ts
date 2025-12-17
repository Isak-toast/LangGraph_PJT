import { defineStore } from 'pinia'
import { ref } from 'vue'
import { streamChat } from '../services/api'

export interface Message {
    id: number;
    role: 'user' | 'ai';
    content: string;
    thoughts?: string[]; // Log of active nodes
    activeNode?: string | null; // Currently executing node
    timestamp: number;
}

export const useChatStore = defineStore('chat', () => {
    const messages = ref<Message[]>([]);
    const isLoading = ref(false);
    const threadId = ref(`thread_${Date.now()}`);

    // Add message and return ID
    const addMessage = (role: 'user' | 'ai', content: string): number => {
        const id = Date.now();
        messages.value.push({
            id,
            role,
            content,
            thoughts: [],
            timestamp: Date.now(),
        });
        return id;
    };

    const updateMessageContent = (id: number, content: string) => {
        const msg = messages.value.find(m => m.id === id);
        if (msg) msg.content += content;
    };

    const updateMessageNode = (id: number, node: string, isStart: boolean) => {
        const msg = messages.value.find(m => m.id === id);
        if (msg) {
            if (isStart) {
                msg.activeNode = node;
                msg.thoughts?.push(`${node}...`); // Log thought
            } else {
                msg.activeNode = null;
            }
        }
    };

    const sendMessage = async (text: string) => {
        if (!text.trim()) return;

        addMessage('user', text);
        isLoading.value = true;

        // Create AI message placeholder
        const aiMsgId = addMessage('ai', "");

        await streamChat(
            { message: text, thread_id: threadId.value },
            (event) => {
                if (event.type === 'token') {
                    updateMessageContent(aiMsgId, event.content);
                } else if (event.type === 'node_start') {
                    updateMessageNode(aiMsgId, event.node, true);
                } else if (event.type === 'node_end') {
                    updateMessageNode(aiMsgId, event.node, false);
                } else if (event.type === 'error') {
                    updateMessageContent(aiMsgId, `\n[Error: ${event.content}]`);
                }
            },
            (err) => {
                console.error("Stream error", err);
                isLoading.value = false;
                updateMessageContent(aiMsgId, `\n[System Error: ${err}]`);
            },
            () => {
                isLoading.value = false;
            }
        );
    };

    return {
        messages,
        isLoading,
        threadId,
        sendMessage
    }
})
