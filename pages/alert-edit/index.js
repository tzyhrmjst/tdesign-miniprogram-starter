import { createAlert, fetchAlerts, updateAlert } from '~/api/gold';
import { ensureWechatIdentity } from '~/api/auth';
import { subscribeTemplateId } from '~/config/wechat';
import { directionText, unitText } from '~/utils/gold';

const defaultForm = {
  name: '',
  direction: 'above',
  target_price: '',
  unit: 'cny_g',
  cooldown_minutes: 720,
  enabled: true,
};

Page({
  data: {
    id: '',
    statusHeight: 0,
    autoNameEnabled: true,
    form: { ...defaultForm },
    directionOptions: [
      { label: '高于某价格提醒', value: 'above' },
      { label: '低于某价格提醒', value: 'below' },
    ],
  },

  onReady() {
    this.setData({ statusHeight: wx.getWindowInfo().statusBarHeight });
  },

  goBack() {
    wx.navigateBack({ delta: 1 });
  },

  async onLoad(options) {
    if (!options.id) return;
    const alerts = await fetchAlerts();
    const target = alerts.find((item) => String(item.id) === String(options.id));
    if (target) {
      const autoName = this.buildAutoName(target.direction, target.target_price, target.unit);
      const autoNameEnabled = target.name === autoName;
      this.setData({
        id: options.id,
        autoNameEnabled,
        form: {
          name: autoNameEnabled ? '' : target.name,
          direction: target.direction,
          target_price: String(target.target_price),
          unit: target.unit,
          cooldown_minutes: target.cooldown_minutes,
          enabled: target.enabled,
        },
      });
    }
  },

  buildAutoName(direction, targetPrice, unit) {
    return `${directionText(direction)} ${Number(targetPrice)} ${unitText(unit)}提醒`;
  },

  onInput(e) {
    const { field } = e.currentTarget.dataset;
    const { value } = e.detail;
    const data = { [`form.${field}`]: value };
    if (field === 'name') {
      data.autoNameEnabled = !String(value).trim();
    }
    this.setData(data);
  },

  onDirectionChange(e) {
    this.setData({ 'form.direction': e.detail.value });
  },

  onEnabledChange(e) {
    this.setData({ 'form.enabled': e.detail.value });
  },

  buildPayload() {
    const { autoNameEnabled, form } = this.data;
    const targetPrice = Number(form.target_price);
    const cooldown = Number(form.cooldown_minutes);
    if (!targetPrice || targetPrice <= 0) {
      wx.showToast({ title: '价格必须大于 0', icon: 'none' });
      return null;
    }
    if (!Number.isInteger(cooldown) || cooldown <= 0) {
      wx.showToast({ title: '冷却时间需为正整数', icon: 'none' });
      return null;
    }
    const name = autoNameEnabled || !String(form.name).trim()
      ? this.buildAutoName(form.direction, targetPrice, form.unit)
      : String(form.name).trim();
    return {
      ...form,
      name,
      target_price: targetPrice,
      cooldown_minutes: cooldown,
    };
  },

  requestSubscribe() {
    if (this.data.id || !subscribeTemplateId || !wx.requestSubscribeMessage) {
      return Promise.resolve();
    }
    return new Promise((resolve) => {
      wx.requestSubscribeMessage({
        tmplIds: [subscribeTemplateId],
        success: (res) => {
          if (res[subscribeTemplateId] === 'accept') {
            wx.showToast({ title: '已开启提醒通知', icon: 'success' });
          } else if (res[subscribeTemplateId] === 'reject') {
            wx.showToast({ title: '未开启通知，将无法收到价格提醒', icon: 'none', duration: 3000 });
          }
        },
        fail: () => {
          wx.showToast({ title: '可在「设置 > 订阅消息」中手动开启', icon: 'none', duration: 3000 });
        },
        complete: resolve,
      });
    });
  },

  async onSubmit() {
    const payload = this.buildPayload();
    if (!payload) return;

    try {
      wx.showLoading({ title: '保存中' });

      const identity = await ensureWechatIdentity();
      await this.requestSubscribe();

      if (this.data.id) {
        await updateAlert(this.data.id, payload);
      } else {
        await createAlert({ ...payload, openid: identity.openid });
      }

      wx.hideLoading();
      wx.showToast({ title: '已保存', icon: 'success' });
      setTimeout(() => wx.navigateBack(), 400);
    } catch (err) {
      wx.hideLoading();
      wx.showToast({
        title: err && err.message ? err.message : '保存失败',
        icon: 'none',
      });
    }
  },
});
