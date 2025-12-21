import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ChatMessage from './chat/ChatMessage.vue'

describe('ChatMessage - Agentic Insight Style', () => {
    it('renders user message with bubble style', () => {
        const wrapper = mount(ChatMessage, {
            props: {
                message: {
                    id: 1,
                    role: 'user',
                    content: 'Hello AI',
                    timestamp: Date.now()
                }
            }
        })
        expect(wrapper.find('.gemini-user-message').exists()).toBe(true)
        expect(wrapper.find('.gemini-user-bubble').exists()).toBe(true)
        expect(wrapper.text()).toContain('Hello AI')
    })

    it('renders AI message with content and no user bubble', () => {
        const wrapper = mount(ChatMessage, {
            props: {
                message: {
                    id: 2,
                    role: 'ai',
                    content: 'Hello User',
                    timestamp: Date.now()
                }
            }
        })
        expect(wrapper.find('.gemini-ai-message').exists()).toBe(true)
        expect(wrapper.find('.gemini-ai-content').exists()).toBe(true)
        expect(wrapper.find('.gemini-user-bubble').exists()).toBe(false)
        expect(wrapper.text()).toContain('Hello User')
    })

    it('renders thinking process accordion when thoughts present', () => {
        const wrapper = mount(ChatMessage, {
            props: {
                message: {
                    id: 3,
                    role: 'ai',
                    content: 'Final answer',
                    thoughts: ['Thinking step 1', 'Thinking step 2'],
                    timestamp: Date.now()
                }
            }
        })
        expect(wrapper.text()).toContain('사고 과정 보기')
    })
})
