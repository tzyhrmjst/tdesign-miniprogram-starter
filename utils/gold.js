const OUNCE_TO_GRAM = 31.1035;
const OPENID_KEY = 'gold_openid';
const OPENID_SOURCE_KEY = 'gold_openid_source';
const DEMO_OPENID_KEY = 'gold_demo_openid';

export const getOpenidSource = () => wx.getStorageSync(OPENID_SOURCE_KEY) || 'demo';

export const setOpenid = (openid, source = 'demo') => {
  wx.setStorageSync(OPENID_KEY, openid);
  wx.setStorageSync(OPENID_SOURCE_KEY, source);
};

export const getFallbackOpenid = () => {
  let openid = wx.getStorageSync(DEMO_OPENID_KEY);
  if (!openid) {
    openid = `demo_${Date.now()}`;
    wx.setStorageSync(DEMO_OPENID_KEY, openid);
  }
  return openid;
};

export const getOpenid = () => {
  let openid = wx.getStorageSync(OPENID_KEY);
  if (!openid) {
    openid = getFallbackOpenid();
    setOpenid(openid, 'demo');
  }
  return openid;
};

export const formatPrice = (value, digits = 2) => {
  const numberValue = Number(value);
  if (!Number.isFinite(numberValue)) return '--';
  return numberValue.toFixed(digits);
};

export const formatSigned = (value, digits = 2) => {
  const numberValue = Number(value);
  if (!Number.isFinite(numberValue)) return '--';
  const sign = numberValue > 0 ? '+' : '';
  return `${sign}${numberValue.toFixed(digits)}`;
};

export const formatTime = (value) => {
  if (!value) return '--';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  const pad = (num) => String(num).padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(
    date.getMinutes(),
  )}`;
};

export const unitText = (unit) => (unit === 'cny_g' ? '人民币/克' : '美元/盎司');

export const unitSymbol = (unit) => (unit === 'cny_g' ? '¥' : '$');

export const directionText = (direction) => (direction === 'below' ? '低于' : '高于');

export const normalizeLatest = (data = {}) => {
  const priceUsdOz = Number(data.price_usd_oz || data.price || 0);
  const priceCnyG = Number(data.price_cny_g || ((priceUsdOz * 7.2) / OUNCE_TO_GRAM).toFixed(2));
  return {
    symbol: data.symbol || 'XAU',
    price_usd_oz: priceUsdOz,
    price_cny_g: priceCnyG,
    buyback_price_cny_g: Number(data.buyback_price_cny_g || 0),
    change: Number(data.change || data.change_value || 0),
    change_percent: Number(data.change_percent || 0),
    updated_at: data.updated_at || data.updatedAt || new Date().toISOString(),
    source: data.source || 'gold-api.com',
  };
};
