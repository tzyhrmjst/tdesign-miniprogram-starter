import { fetchLatestGold } from '~/api/gold';
import { formatPrice, formatSigned, formatTime, normalizeLatest } from '~/utils/gold';

Page({
  data: {
    loading: true,
    refreshing: false,
    error: '',
    price: null,
    displayPrice: '--',
    displayBuybackPrice: '--',
    changeText: '--',
    changePercentText: '--',
    changeClass: 'flat',
    updatedAtText: '--',
  },

  onLoad() {
    this._animTimers = {};
    this.loadLatest();
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

  onRefresh() {
    this.setData({ refreshing: true });
    this.loadLatest();
  },

  applyPrice(price, instant = false) {
    if (!price) return;

    const salePrice = price.price_cny_g;
    const buybackPrice = price.buyback_price_cny_g || salePrice;
    const change = Number(price.change || 0);
    let changeClass = 'flat';
    if (change > 0) changeClass = 'up';
    if (change < 0) changeClass = 'down';

    const saleStart = parseFloat(this.data.displayPrice);
    const buybackStart = parseFloat(this.data.displayBuybackPrice);

    this.setData({
      price,
      changeText: formatSigned(change),
      changePercentText: `${formatSigned(price.change_percent)}%`,
      changeClass,
      updatedAtText: formatTime(price.updated_at),
    });

    if (instant || isNaN(saleStart)) {
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
      const eased = 1 - Math.pow(1 - progress, 3);
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
