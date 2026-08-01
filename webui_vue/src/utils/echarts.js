/**
 * echarts on-demand import module.
 * Only registers chart types and components actually used in this project:
 * - RadarChart    (StudentAnalytics, LearningPath, DataLab)
 * - SunburstChart (ResearchHotspot)
 * - ScatterChart  (DataLab)
 * - BarChart      (DataLab)
 * - BoxplotChart  (DataLab)
 * - HeatmapChart  (DataLab)
 * - ParallelChart (DataLab)
 */
import * as echarts from 'echarts/core'

import {
  RadarChart,
  SunburstChart,
  ScatterChart,
  BarChart,
  LineChart,
  PieChart,
  BoxplotChart,
  HeatmapChart,
  ParallelChart,
} from 'echarts/charts'

import {
  TooltipComponent,
  LegendComponent,
  GridComponent,
  ParallelComponent,
  DatasetComponent,
  VisualMapComponent,
} from 'echarts/components'

import { CanvasRenderer } from 'echarts/renderers'

echarts.use([
  // Charts
  RadarChart,
  SunburstChart,
  ScatterChart,
  BarChart,
  LineChart,
  PieChart,
  BoxplotChart,
  HeatmapChart,
  ParallelChart,
  // Components
  TooltipComponent,
  LegendComponent,
  GridComponent,
  ParallelComponent,
  DatasetComponent,
  VisualMapComponent,
  // Renderer
  CanvasRenderer,
])

export default echarts
