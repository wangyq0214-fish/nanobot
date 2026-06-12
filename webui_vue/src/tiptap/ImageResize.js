import Image from '@tiptap/extension-image'
import { VueNodeViewRenderer } from '@tiptap/vue-3'
import ImageResizeView from './ImageResizeView.vue'

export const ImageResize = Image.extend({
  name: 'imageResize',
  inline: true,
  group: 'inline',

  addAttributes() {
    return {
      ...this.parent?.(),
      width: { default: null },
      height: { default: null },
    }
  },

  addNodeView() {
    return VueNodeViewRenderer(ImageResizeView)
  },
})
