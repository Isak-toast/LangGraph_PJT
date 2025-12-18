import { defineStore } from 'pinia'
import { ref, watch, computed } from 'vue'
import { streamChat } from '../services/api'

export interface Message {
    id: number;
    role: 'user' | 'ai';
    content: string;
    thoughts?: string[];
    activeNode?: string | null;
    timestamp: number;
}

export interface Session {
    id: string;
    title: string;
    messages: Message[];
    createdAt: number;
    updatedAt: number;
}

const STORAGE_KEY = 'agentic_insight_sessions';
const CURRENT_SESSION_KEY = 'agentic_insight_current_session';

// Load sessions from localStorage
const loadSessions = (): Session[] => {
    try {
        const stored = localStorage.getItem(STORAGE_KEY);
        return stored ? JSON.parse(stored) : [];
    } catch {
        return [];
    }
};

// Load current session ID from localStorage
const loadCurrentSessionId = (): string | null => {
    return localStorage.getItem(CURRENT_SESSION_KEY);
};

export const useChatStore = defineStore('chat', () => {
    // Session management
    const sessions = ref<Session[]>(loadSessions());
    const currentSessionId = ref<string | null>(loadCurrentSessionId());

    // Current session state
    const messages = ref<Message[]>([]);
    const isLoading = ref(false);
    const threadId = ref(`thread_${Date.now()}`);

    // Computed: current session
    const currentSession = computed(() => {
        return sessions.value.find(s => s.id === currentSessionId.value) || null;
    });

    // Auto-save sessions to localStorage
    watch(sessions, (newSessions) => {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(newSessions));
    }, { deep: true });

    // Save current session ID to localStorage
    watch(currentSessionId, (newId) => {
        if (newId) {
            localStorage.setItem(CURRENT_SESSION_KEY, newId);
        } else {
            localStorage.removeItem(CURRENT_SESSION_KEY);
        }
    });

    // Generate session title from first message
    const generateTitle = (text: string): string => {
        const maxLen = 30;
        if (text.length <= maxLen) return text;
        return text.substring(0, maxLen) + '...';
    };

    // Create a new session
    const createNewSession = (): string => {
        const newSession: Session = {
            id: `session_${Date.now()}`,
            title: '새 채팅',
            messages: [],
            createdAt: Date.now(),
            updatedAt: Date.now(),
        };
        sessions.value.unshift(newSession);
        currentSessionId.value = newSession.id;
        messages.value = [];
        threadId.value = `thread_${Date.now()}`;
        return newSession.id;
    };

    // Switch to an existing session
    const switchSession = (sessionId: string) => {
        const session = sessions.value.find(s => s.id === sessionId);
        if (session) {
            currentSessionId.value = sessionId;
            messages.value = [...session.messages];
            threadId.value = session.id;
        }
    };

    // Delete a session
    const deleteSession = (sessionId: string) => {
        const index = sessions.value.findIndex(s => s.id === sessionId);
        if (index !== -1) {
            sessions.value.splice(index, 1);
            if (currentSessionId.value === sessionId) {
                if (sessions.value.length > 0) {
                    switchSession(sessions.value[0].id);
                } else {
                    currentSessionId.value = null;
                    messages.value = [];
                }
            }
        }
    };

    // Sync current messages back to session
    const syncToSession = () => {
        if (currentSessionId.value) {
            const session = sessions.value.find(s => s.id === currentSessionId.value);
            if (session) {
                session.messages = [...messages.value];
                session.updatedAt = Date.now();

                // Update title from first user message if still default
                if (session.title === '새 채팅' && messages.value.length > 0) {
                    const firstUserMsg = messages.value.find(m => m.role === 'user');
                    if (firstUserMsg) {
                        session.title = generateTitle(firstUserMsg.content);
                    }
                }
            }
        }
    };

    // Add message and return ID
    const addMessage = (role: 'user' | 'ai', content: string): number => {
        // Auto-create session if none exists
        if (!currentSessionId.value) {
            createNewSession();
        }

        const id = Date.now();
        messages.value.push({
            id,
            role,
            content,
            thoughts: [],
            timestamp: Date.now(),
        });
        syncToSession();
        return id;
    };

    const updateMessageContent = (id: number, content: string) => {
        const msg = messages.value.find(m => m.id === id);
        if (msg) {
            msg.content += content;
            syncToSession();
        }
    };

    // Node descriptions for meaningful thinking process
    const nodeDescriptions: Record<string, { start: string; end: string }> = {
        'Supervisor': {
            start: '🧠 Supervisor가 작업을 분석하고 다음 에이전트를 결정 중...',
            end: '✅ Supervisor가 라우팅 결정 완료'
        },
        'Researcher': {
            start: '🔍 Researcher가 관련 정보를 검색 중...',
            end: '✅ Researcher가 검색 결과 수집 완료'
        },
        'Writer': {
            start: '✍️ Writer가 응답을 작성 중...',
            end: '✅ Writer가 콘텐츠 작성 완료'
        }
    };

    const updateMessageNode = (id: number, node: string, isStart: boolean) => {
        const msg = messages.value.find(m => m.id === id);
        if (msg) {
            const desc = nodeDescriptions[node];
            const timestamp = new Date().toLocaleTimeString('ko-KR', {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });

            if (isStart) {
                msg.activeNode = node;
                const thought = desc?.start || `⏳ ${node} 실행 중...`;
                msg.thoughts?.push(`[${timestamp}] ${thought}`);
            } else {
                msg.activeNode = null;
                const thought = desc?.end || `✅ ${node} 완료`;
                // Update the last thought for this node instead of adding new
                const lastThoughtIdx = msg.thoughts?.findIndex(t => t.includes(node) && t.includes('중...'));
                if (lastThoughtIdx !== undefined && lastThoughtIdx >= 0 && msg.thoughts) {
                    msg.thoughts[lastThoughtIdx] = `[${timestamp}] ${thought}`;
                }
            }
            syncToSession();
        }
    };

    const sendMessage = async (text: string) => {
        if (!text.trim()) return;

        addMessage('user', text);
        isLoading.value = true;

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

    // Initialize: load last session or create new one
    const initialize = () => {
        if (currentSessionId.value) {
            const session = sessions.value.find(s => s.id === currentSessionId.value);
            if (session) {
                messages.value = [...session.messages];
                threadId.value = session.id;
            }
        }
    };

    // Call initialize on store creation
    initialize();

    return {
        // State
        messages,
        isLoading,
        threadId,
        sessions,
        currentSessionId,
        currentSession,

        // Actions
        sendMessage,
        createNewSession,
        switchSession,
        deleteSession,
    }
})
