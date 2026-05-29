Component({
  options: {
    styleIsolation: 'shared',
  },
  properties: {
    titleText: String,
  },
  data: {
    statusHeight: 0,
  },
  lifetimes: {
    ready() {
      this.setData({ statusHeight: wx.getWindowInfo().statusBarHeight });
    },
  },
});
