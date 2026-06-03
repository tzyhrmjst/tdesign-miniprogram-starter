import * as echarts from './echarts';

Component({
  options: {
    styleIsolation: 'apply-shared',
  },
  properties: {
    ec: { type: Object },
    canvasId: { type: String, value: 'ec-canvas' },
    isUseNewCanvas: { type: Boolean, value: true },
    forceUseOldCanvas: { type: Boolean, value: false },
  },
  data: {
    echarts,
  },
});
