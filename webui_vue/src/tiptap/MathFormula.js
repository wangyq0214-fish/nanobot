import { Node, mergeAttributes } from '@tiptap/core'
import { VueNodeViewRenderer } from '@tiptap/vue-3'
import MathFormulaView from './MathFormulaView.vue'

export const MathFormula = Node.create({
  name: 'mathFormula',
  group: 'inline',
  inline: true,
  atom: true,

  addAttributes() {
    return {
      formula: { default: 'E = mc^2' },
      displayMode: { default: false },
    }
  },

  parseHTML() {
    return [
      {
        tag: 'span[data-math-inline]',
        getAttrs: (el) => ({
          formula: el.getAttribute('data-formula'),
          displayMode: false,
        }),
      },
      {
        tag: 'div[data-math-block]',
        getAttrs: (el) => ({
          formula: el.getAttribute('data-formula'),
          displayMode: true,
        }),
      },
    ]
  },

  renderHTML({ HTMLAttributes }) {
    const dm = HTMLAttributes.displayMode
    const tag = dm ? 'div' : 'span'
    return [
      tag,
      mergeAttributes(HTMLAttributes, {
        'data-formula': HTMLAttributes.formula,
        'data-math-inline': dm ? undefined : '',
        'data-math-block': dm ? '' : undefined,
      }),
    ]
  },

  addNodeView() {
    return VueNodeViewRenderer(MathFormulaView)
  },
})
