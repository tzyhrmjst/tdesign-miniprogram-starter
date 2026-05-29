import { deleteAlert, fetchAlerts, updateAlertStatus } from '~/api/gold';
import { directionText, formatPrice, formatTime, unitSymbol, unitText } from '~/utils/gold';

Page({
  data: {
    loading: true,
    alerts: [],
  },

  onLoad() {
    this.loadAlerts();
  },

  onShow() {
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setData({ value: 'alerts' });
    }
    this.loadAlerts();
  },

  async loadAlerts() {
    this.setData({ loading: true });
    try {
      const alerts = await fetchAlerts();
      this.setData({
        alerts: alerts.map((item) => ({
          ...item,
          directionText: directionText(item.direction),
          unitText: unitText(item.unit),
          unitSymbol: unitSymbol(item.unit),
          targetText: formatPrice(item.target_price),
          lastTriggeredText: item.last_triggered_at ? formatTime(item.last_triggered_at) : '暂未触发',
        })),
      });
    } catch (err) {
      wx.showToast({ title: '提醒列表获取失败', icon: 'none' });
    } finally {
      this.setData({ loading: false });
    }
  },

  goCreate() {
    wx.navigateTo({ url: '/pages/alert-edit/index' });
  },

  goEdit(e) {
    const { id } = e.currentTarget.dataset;
    wx.navigateTo({ url: `/pages/alert-edit/index?id=${id}` });
  },

  async onToggle(e) {
    const { id } = e.currentTarget.dataset;
    const { value } = e.detail;
    try {
      await updateAlertStatus(id, value);
      this.loadAlerts();
    } catch (err) {
      wx.showToast({ title: '状态更新失败', icon: 'none' });
    }
  },

  onDelete(e) {
    const { id } = e.currentTarget.dataset;
    wx.showModal({
      title: '删除提醒',
      content: '确认删除这条价格提醒？',
      success: async (res) => {
        if (!res.confirm) return;
        try {
          await deleteAlert(id);
          wx.showToast({ title: '已删除', icon: 'success' });
          this.loadAlerts();
        } catch (err) {
          wx.showToast({ title: '删除失败', icon: 'none' });
        }
      },
    });
  },
});
