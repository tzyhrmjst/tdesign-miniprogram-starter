const now = new Date().toISOString();

let alerts = [
  {
    id: 1,
    openid: 'demo',
    name: '高于 4600 美元提醒',
    direction: 'above',
    target_price: 4600,
    unit: 'usd_oz',
    cooldown_minutes: 720,
    enabled: true,
    last_triggered_at: null,
    created_at: now,
  },
];

const histories = [
  {
    id: 1,
    rule_id: 1,
    rule_name: '高于 4600 美元提醒',
    openid: 'demo',
    trigger_price: 4601.2,
    target_price: 4600,
    direction: 'above',
    unit: 'usd_oz',
    message: '黄金价格提醒已触发',
    triggered_at: now,
  },
];

const ok = (data) => ({ code: 200, success: true, data });

export default [
  {
    path: '/api/gold/latest',
    data: {
      symbol: 'SALE_XAU_CNY_G',
      price_usd_oz: 4451.7,
      price_cny_g: 975.93,
      change: 0,
      change_percent: 0,
      updated_at: now,
      source: '国际金价折算 + 销售溢价2.86',
    },
  },
  {
    path: '/api/gold/history',
    data: [
      { ts: now, price_usd_oz: 4451.7, price_cny_g: 975.93 },
      { ts: '2026-05-19T10:00:00Z', price_usd_oz: 4448.1, price_cny_g: 975.14 },
    ],
  },
  {
    path: '/api/alerts',
    data: alerts,
  },
  {
    path: '/api/alert-history',
    data: histories,
  },
  {
    path: '/api/alerts/create',
    response(data) {
      const record = {
        id: Date.now(),
        last_triggered_at: null,
        created_at: new Date().toISOString(),
        ...data,
      };
      alerts = [record, ...alerts];
      return ok(record);
    },
  },
];
