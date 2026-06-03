import { fetchLatestGold, fetchKline } from '~/api/gold';
import { formatPrice, formatTime, normalizeLatest } from '~/utils/gold';
import * as echarts from '../../components/ec-canvas/echarts';

// echarts is imported at module scope for use in initChart (called by ec-canvas component)

let chartInstance = null;
let pendingKlineData = null;

function buildOption(dates, prices) {
  return {
    backgroundColor: '#1b1d1f',
    animation: false,
    grid: {
      left: 10,
      right: 12,
      top: 8,
      bottom: 4,
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLine: { lineStyle: { color: 'rgba(248,243,231,0.12)' } },
      axisLabel: { color: 'rgba(248,243,231,0.4)', fontSize: 9 },
      axisTick: { show: false },
      splitLine: { show: false },
    },
    yAxis: {
      type: 'value',
      scale: true,
      axisLabel: {
        color: 'rgba(248,243,231,0.4)',
        fontSize: 9,
        formatter: (v) => `¥${v.toFixed(0)}`,
      },
      splitLine: { lineStyle: { color: 'rgba(248,243,231,0.06)' } },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    tooltip: {
      trigger: 'axis',
      confine: true,
      backgroundColor: 'rgba(27,29,31,0.92)',
      borderColor: 'rgba(64,201,139,0.3)',
      textStyle: { color: '#f8f3e7', fontSize: 11 },
      formatter(params) {
        const p = params[0];
        return `${p.name}  ¥${Number(p.value).toFixed(2)}`;
      },
    },
    series: [
      {
        type: 'line',
        data: prices,
        smooth: true,
        symbol: 'none',
        lineStyle: { color: '#40c98b', width: 1.5 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(64,201,139,0.18)' },
            { offset: 1, color: 'rgba(64,201,139,0.02)' },
          ]),
        },
      },
    ],
  };
}

function applyKlineToChart(data) {
  if (!data || !data.length) {
    return;
  }
  if (!chartInstance) {
    pendingKlineData = data;
    return;
  }
  const dates = data.map((d) => {
    const t = d.ts || '';
    return t.length >= 16 ? t.substring(11, 16) : t;
  });
  const prices = data.map((d) => d.close);

  chartInstance.setOption(buildOption(dates, prices), true);
}

function initChart(canvas, width, height, dpr) {
  if (!width || !height) {
    width = width || 320;
    height = height || 220;
  }

  const chart = echarts.init(canvas, null, {
    width,
    height,
    devicePixelRatio: dpr,
  });
  canvas.setChart(chart);

  chart.setOption(buildOption([], []));
  chartInstance = chart;

  // test: resize to make sure canvas renders
  try { chart.resize({ width, height }); } catch (_) { /* ignore */ }

  if (pendingKlineData) {
    const data = pendingKlineData;
    pendingKlineData = null;
    applyKlineToChart(data);
  }

  return chart;
}

Page({
  data: {
    loading: true,
    refreshing: false,
    error: '',
    price: null,
    displayPrice: '--',
    displayBuybackPrice: '--',
    updatedAtText: '--',
    klineLoading: true,
    klineError: '',
    ec: {
      onInit: initChart,
    },
    klineData: [],
  },

  onLoad() {
    this._animTimers = {};
    this.loadLatest();
    setTimeout(() => this.loadKline(), 100);
    this._startPolling();
  },

  onShow() {
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setData({ value: 'home' });
    }
    this._startPolling();
  },

  onHide() {
    this._clearAnims();
    this._stopPolling();
  },

  onUnload() {
    this._clearAnims();
    this._stopPolling();
    chartInstance = null;
    pendingKlineData = null;
  },

  _startPolling() {
    this._stopPolling();
    this.pollTimer = setInterval(() => this.loadLatest(true), 10 * 1000);
  },

  _stopPolling() {
    if (this.pollTimer) {
      clearInterval(this.pollTimer);
      this.pollTimer = null;
    }
  },

  _clearAnims() {
    Object.values(this._animTimers || {}).forEach(clearInterval);
    this._animTimers = {};
  },

  async loadLatest(silent = false) {
    if (!silent) this.setData({ loading: true, error: '' });
    try {
      const latest = normalizeLatest(await fetchLatestGold());
      this.applyPrice(latest);
    } catch (err) {
      if (!silent) {
        this.setData({ error: '暂时无法获取最新价格，请稍后再试' });
      }
    } finally {
      this.setData({ loading: false, refreshing: false });
    }
  },

  async loadKline() {
    this.setData({ klineLoading: true, klineError: '' });
    try {
      const data = await fetchKline(5, 288, 'buyback');
      if (!data || !data.length) {
        this.setData({ klineData: [], klineError: '快照数据不足，稍后自动生成' });
        return;
      }
      this.setData({ klineData: data });
      applyKlineToChart(data);
    } catch (err) {
      this.setData({ klineError: '暂时无法加载K线' });
    } finally {
      this.setData({ klineLoading: false });
    }
  },

  onRefresh() {
    this.setData({ refreshing: true });
    this.loadLatest();
    this.loadKline();
  },

  applyPrice(price, instant = false) {
    if (!price) return;

    const salePrice = price.price_cny_g;
    const buybackPrice = price.buyback_price_cny_g || salePrice;

    const saleStart = parseFloat(this.data.displayPrice);
    const buybackStart = parseFloat(this.data.displayBuybackPrice);

    this.setData({
      price,
      updatedAtText: formatTime(price.updated_at),
    });

    if (instant || Number.isNaN(saleStart)) {
      this.setData({
        displayPrice: formatPrice(salePrice, 2),
        displayBuybackPrice: formatPrice(buybackPrice, 2),
      });
      return;
    }

    this._animateValue('displayPrice', saleStart, salePrice, 2);
    this._animateValue('displayBuybackPrice', buybackStart, buybackPrice, 2);
  },

  _animateValue(key, startVal, endVal, decimals) {
    if (startVal === endVal) return;

    if (this._animTimers[key]) {
      clearInterval(this._animTimers[key]);
    }

    const startTime = Date.now();
    const duration = 600;
    const range = endVal - startVal;

    this._animTimers[key] = setInterval(() => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - (1 - progress) ** 3;
      const current = startVal + range * eased;

      this.setData({ [key]: current.toFixed(decimals) });

      if (progress >= 1) {
        clearInterval(this._animTimers[key]);
        delete this._animTimers[key];
        this.setData({ [key]: endVal.toFixed(decimals) });
      }
    }, 33);
  },

  goCreateAlert() {
    wx.navigateTo({ url: '/pages/alert-edit/index' });
  },

  goHistory() {
    wx.switchTab({ url: '/pages/history/index' });
  },
});
