import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ChatMessage from './chat/ChatMessage.vue'

describe('ChatMessage - Gemini Style', () => {
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
        // User message should have bubble class and content
        expect(wrapper.find('.gemini-user-message').exists()).toBe(true)
        expect(wrapper.find('.gemini-user-bubble').exists()).toBe(true)
        expect(wrapper.text()).toContain('Hello AI')
    })

    it('renders AI message with avatar and no bubble', () => {
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
        // AI message should have avatar but NO bubble background
        expect(wrapper.find('.gemini-ai-message').exists()).toBe(true)
        expect(wrapper.find('.gemini-ai-avatar').exists()).toBe(true)
        expect(wrapper.find('.gemini-ai-content').exists()).toBe(true)
        // Should NOT have user bubble class
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
        // Should have thinking button
        expect(wrapper.text()).toContain('사고 과정 보기')
    })
})
