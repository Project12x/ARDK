
import { ReactRenderer } from '@tiptap/react'
import tippy from 'tippy.js'

import { MentionList } from './MentionList'
import { GlobalSearch } from '../../../lib/search'

 
type SuggestionProps = any

export default {
    items: async ({ query }: { query: string }) => {
        if (!query) return []
        const results = await GlobalSearch.search(query)
        return results.filter((r) => r.type !== 'action').slice(0, 10)
    },

    render: () => {
        let component: ReactRenderer
         
        let popup: any

        return {
            onStart: (props: SuggestionProps) => {
                component = new ReactRenderer(MentionList, {
                    props,
                    editor: props.editor,
                })

                if (!props.clientRect) {
                    return
                }

                popup = tippy('body', {
                    getReferenceClientRect: props.clientRect,
                    appendTo: () => document.body,
                    content: component.element,
                    showOnCreate: true,
                    interactive: true,
                    trigger: 'manual',
                    placement: 'bottom-start',
                })
            },

            onUpdate(props: SuggestionProps) {
                component.updateProps(props)

                if (!props.clientRect) {
                    return
                }

                popup[0].setProps({
                    getReferenceClientRect: props.clientRect,
                })
            },

            onKeyDown(props: SuggestionProps) {
                if (props.event.key === 'Escape') {
                    popup[0].hide()
                    return true
                }

                 
                return (component.ref as any)?.onKeyDown(props)
            },

            onExit() {
                popup[0].destroy()
                component.destroy()
            },
        }
    },
}
