// app.js
import config from './config';
import Mock from './mock/index';
import createBus from './utils/eventBus';

if (config.isMock) {
  Mock();
}

App({
  onLaunch() {
    const updateManager = wx.getUpdateManager();

    updateManager.onCheckForUpdate((res) => {
      // console.log(res.hasUpdate)
    });

    updateManager.onUpdateReady(() => {
      wx.showModal({
        title: '更新提示',
        content: '新版本已经准备好，是否重启应用？',
        success(res) {
          if (res.confirm) {
            updateManager.applyUpdate();
          }
        },
      });
    });

    this.setUnreadNum(0);
  },
  globalData: {
    userInfo: null,
    unreadNum: 0,
    openid: '',
    openidSource: 'demo',
  },

  /** 全局事件总线 */
  eventBus: createBus(),

  /** 设置未读消息数量 */
  setUnreadNum(unreadNum) {
    this.globalData.unreadNum = unreadNum;
    this.eventBus.emit('unread-num-change', unreadNum);
  },
});
