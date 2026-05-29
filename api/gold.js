import request from './request';
import config from '~/config';
import { getOpenid, getOpenidSource } from '~/utils/gold';

const ALERT_KEY = 'gold_mock_alerts';
const HISTORY_KEY = 'gold_mock_histories';

const initialAlerts = () => [
  {
    id: 1,
    name: '高于 4600 美元提醒',
    direction: 'above',
    target_price: 4600,
    unit: 'usd_oz',
    cooldown_minutes: 720,
    enabled: true,
    last_triggered_at: null,
    created_at: new Date().toISOString(),
  },
];

const getMockAlerts = () => {
  const stored = wx.getStorageSync(ALERT_KEY);
  if (stored && stored.length) return stored;
  const seed = initialAlerts();
  wx.setStorageSync(ALERT_KEY, seed);
  return seed;
};

const setMockAlerts = (alerts) => {
  wx.setStorageSync(ALERT_KEY, alerts);
  return alerts;
};

export const fetchLatestGold = () => request('/api/gold/latest').then((res) => res.data.data || res.data);

export const fetchPriceHistory = (range = '1d') => request('/api/gold/history', 'GET', { range }).then((res) => res.data.data || []);

export const fetchAlerts = () => {
  if (config.isMock) return Promise.resolve(getMockAlerts());
  return request('/api/alerts', 'GET', { openid: getOpenid() }).then((res) => res.data.data || []);
};

export const createAlert = (payload) => {
  if (config.isMock) {
    const record = {
      id: Date.now(),
      last_triggered_at: null,
      created_at: new Date().toISOString(),
      ...payload,
    };
    setMockAlerts([record, ...getMockAlerts()]);
    return Promise.resolve(record);
  }
  const openid = payload.openid || getOpenid();
  if (getOpenidSource() !== 'wechat') {
    return Promise.reject(new Error('请先登录后再保存提醒'));
  }
  return request('/api/alerts', 'POST', {
    openid,
    ...payload,
  }).then((res) => res.data.data || res.data);
};

export const updateAlert = (id, payload) => {
  if (config.isMock) {
    const alerts = getMockAlerts().map((item) => (String(item.id) === String(id) ? { ...item, ...payload } : item));
    setMockAlerts(alerts);
    return Promise.resolve(alerts.find((item) => String(item.id) === String(id)));
  }
  return request(`/api/alerts/${id}`, 'PUT', {
    openid: getOpenid(),
    ...payload,
  }).then((res) => res.data.data);
};

export const updateAlertStatus = (id, enabled) => {
  if (config.isMock) return updateAlert(id, { enabled });
  return request(`/api/alerts/${id}/status`, 'PATCH', {
    openid: getOpenid(),
    enabled,
  }).then((res) => res.data.data);
};

export const deleteAlert = (id) => {
  if (config.isMock) {
    setMockAlerts(getMockAlerts().filter((item) => String(item.id) !== String(id)));
    return Promise.resolve({ success: true });
  }
  return request(`/api/alerts/${id}?openid=${encodeURIComponent(getOpenid())}`, 'DELETE').then((res) => res.data);
};

export const fetchAlertHistory = () => {
  if (config.isMock) {
    const stored = wx.getStorageSync(HISTORY_KEY);
    if (stored && stored.length) return Promise.resolve(stored);
  }
  return request('/api/alert-history', 'GET', { openid: getOpenid() }).then((res) => res.data.data || []);
};
