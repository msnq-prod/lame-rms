import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: 5,
  duration: '30s',
  thresholds: {
    http_req_duration: ['p(95)<800'],
    http_req_failed: ['rate<0.01'],
  },
};

const BASE_URL = `${__ENV.API_BASE_URL || 'http://127.0.0.1:8000/api'}`;

export default function () {
  const listResponse = http.get(`${BASE_URL}/assets`);
  check(listResponse, {
    'list status is 200': (r) => r.status === 200,
  });

  try {
    const data = listResponse.json();
    if (data.items && data.items.length > 0) {
      const assetId = data.items[0].id;
      const detail = http.get(`${BASE_URL}/assets/${assetId}`);
      check(detail, {
        'detail status is 200': (r) => r.status === 200,
      });
    }
  } catch (err) {
    // Ignore JSON parsing issues during load to keep the scenario resilient.
  }

  sleep(1);
}
