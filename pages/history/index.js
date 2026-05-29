import { fetchAlertHistory } from '~/api/gold';
import { directionText, formatPrice, formatTime, unitSymbol, unitText } from '~/utils/gold';

Page({
  data: {
    loading: true,
    histories: [],
  },

  onLoad() {
    this.loadHistory();
  },

  onShow() {
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setData({ value: 'history' });
    }
    this.loadHistory();
  },

  async loadHistory() {
    this.setData({ loading: true });
    try {
      const histories = await fetchAlertHistory();
      this.setData({
        histories: histories.map((item) => ({
          ...item,
          timeText: formatTime(item.triggered_at),
          directionText: directionText(item.direction),
          unitText: unitText(item.unit),
          unitSymbol: unitSymbol(item.unit),
          triggerText: formatPrice(item.trigger_price),
          targetText: formatPrice(item.target_price),
        })),
      });
    } catch (err) {
      wx.showToast({ title: '历史记录获取失败', icon: 'none' });
    } finally {
      this.setData({ loading: false });
    }
  },
});
