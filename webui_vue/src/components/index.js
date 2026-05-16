import LessonBasicInfo from './LessonBasicInfo.vue'
import LessonObjectives from './LessonObjectives.vue'
import LessonKeyPoints from './LessonKeyPoints.vue'
import LessonProcess from './LessonProcess.vue'
import LessonBoardDesign from './LessonBoardDesign.vue'
import LessonKnowledgeTree from './LessonKnowledgeTree.vue'
import LessonExercises from './LessonExercises.vue'
import LessonReflection from './LessonReflection.vue'
import MarkdownSection from './MarkdownSection.vue'

// Direct component references — not async wrappers.
// <component :is="..."> resolves synchronously, avoiding issues with
// defineAsyncComponent in v-for loops.
export const sectionComponents = {
  basic_info: LessonBasicInfo,
  objectives: LessonObjectives,
  key_points: LessonKeyPoints,
  teaching_process: LessonProcess,
  board_design: LessonBoardDesign,
  knowledge_tree: LessonKnowledgeTree,
  exercises: LessonExercises,
  reflection: LessonReflection,
  markdown: MarkdownSection,
}

export const FALLBACK_TYPE = 'markdown'
