import request from './request';
import { getFallbackOpenid, setOpenid, getOpenid, getOpenidSource } from '~/utils/gold';

export function loginWithWechat({ allowFallback = true } = {}) {
  return new Promise((resolve, reject) => {
    wx.login({
      success(loginRes) {
        if (!loginRes.code) {
          if (allowFallback) {
            const openid = getFallbackOpenid();
            setOpenid(openid, 'demo');
            resolve({ openid, source: 'demo' });
            return;
          }
          reject(new Error('登录失败，请稍后重试'));
          return;
        }

        request('/api/auth/wx-login', 'POST', { code: loginRes.code })
          .then((res) => {
            const { openid } = res.data.data;
            setOpenid(openid, 'wechat');
            resolve({ openid, source: 'wechat' });
          })
          .catch(() => {
            if (allowFallback) {
              const openid = getFallbackOpenid();
              setOpenid(openid, 'demo');
              resolve({ openid, source: 'demo' });
              return;
            }
            reject(new Error('登录失败，请稍后重试'));
          });
      },
      fail() {
        if (allowFallback) {
          const openid = getFallbackOpenid();
          setOpenid(openid, 'demo');
          resolve({ openid, source: 'demo' });
          return;
        }
        reject(new Error('登录失败，请稍后重试'));
      },
    });
  });
}

export const hasWechatIdentity = () => {
  const openid = getOpenid();
  const source = getOpenidSource();
  return Boolean(openid) && source === 'wechat';
};

export const ensureWechatIdentity = async () => {
  if (hasWechatIdentity()) {
    return { openid: getOpenid(), source: 'wechat' };
  }
  return loginWithWechat({ allowFallback: false });
};
