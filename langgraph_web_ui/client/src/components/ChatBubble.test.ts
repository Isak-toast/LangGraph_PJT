import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ChatBubble from './ChatBubble.vue'

describe('ChatBubble', () => {
    it('renders user message correctly', () => {
        const wrapper = mount(ChatBubble, {
            props: {
                content: 'Hello World',
                role: 'user'
            }
        })
        expect(wrapper.text()).toContain('Hello World')
        expect(wrapper.classes()).toContain('ml-auto') // Tailwind User Class
    })

    it('renders ai message correctly', () => {
        const wrapper = mount(ChatBubble, {
            props: {
                content: '# Title',
                role: 'ai'
            }
        })
        expect(wrapper.html()).toContain('h1') // Markdown rendered
        expect(wrapper.classes()).toContain('bg-muted') // Tailwind AI Class
    })
})
