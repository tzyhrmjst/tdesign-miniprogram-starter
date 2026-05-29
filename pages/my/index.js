import { getOpenid, getOpenidSource } from '~/utils/gold';

Page({
  data: {
    openid: '',
    openidSource: '本地演示用户',
    items: [
      { label: '数据来源', value: '京东金融黄金' },
      { label: '计价单位', value: '人民币/克' },
      { label: '提醒方式', value: '微信服务通知' },
    ],
  },

  onLoad() {
    this.applyIdentity();
    getApp().eventBus.on('identity-ready', () => {
      this.applyIdentity();
    });
  },

  onShow() {
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setData({ value: 'my' });
    }
    this.applyIdentity();
  },

  applyIdentity() {
    const source = getOpenidSource();
    this.setData({
      openid: getOpenid(),
      openidSource: source === 'wechat' ? '微信用户' : '本地演示用户',
    });
  },
});
