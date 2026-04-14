const fs = require('fs');
const http = require('http');

const ADSPOWER_API = 'http://local.adspower.net:50325';
const GROUP_ID = '8671133'; // Tiktok group

// Read proxies from file
const proxies = fs.readFileSync('./downloads/webshare_proxies_2500.txt', 'utf8')
  .trim()
  .split('\n')
  .map(line => {
    const [host, port, user, pass] = line.split(':');
    return { host, port, user, pass };
  });

// Start from proxy 26 (index 25) for profiles tt26-tt275
const START_PROFILE = 26;
const END_PROFILE = 275;

async function makeRequest(url, method = 'GET', body = null) {
  return new Promise((resolve, reject) => {
    const urlObj = new URL(url);
    const options = {
      hostname: urlObj.hostname,
      port: urlObj.port,
      path: urlObj.pathname + urlObj.search,
      method: method,
      headers: {
        'Content-Type': 'application/json'
      }
    };

    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          resolve(JSON.parse(data));
        } catch (e) {
          resolve(data);
        }
      });
    });

    req.on('error', reject);
    if (body) req.write(JSON.stringify(body));
    req.end();
  });
}

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function createProfile(name, proxy) {
  const url = `${ADSPOWER_API}/api/v1/user/create`;

  const body = {
    name: name,
    group_id: GROUP_ID,
    domain_name: 'tiktok.com',
    open_urls: ['https://www.tiktok.com'],
    ipchecker: 'ip2location',
    user_proxy_config: {
      proxy_soft: 'other',
      proxy_type: 'http',
      proxy_host: proxy.host,
      proxy_port: proxy.port,
      proxy_user: proxy.user,
      proxy_password: proxy.pass
    },
    fingerprint_config: {
      automatic_timezone: '1',
      language: ['en-US', 'en']
    }
  };

  const response = await makeRequest(url, 'POST', body);
  return response;
}

async function main() {
  console.log(`Creating profiles tt${START_PROFILE} to tt${END_PROFILE}...`);
  console.log(`Using proxies ${START_PROFILE} to ${END_PROFILE} (total: ${END_PROFILE - START_PROFILE + 1})`);
  console.log(`Group ID: ${GROUP_ID}`);

  let created = 0;
  let failed = 0;

  for (let i = START_PROFILE; i <= END_PROFILE; i++) {
    const profileName = `tt${i}`;
    const proxyIndex = i - 1; // proxy index (0-based)
    const proxy = proxies[proxyIndex];

    if (!proxy) {
      console.log(`No proxy available for ${profileName}`);
      failed++;
      continue;
    }

    try {
      const result = await createProfile(profileName, proxy);

      if (result.code === 0) {
        created++;
        console.log(`[${created}/${END_PROFILE - START_PROFILE + 1}] Created ${profileName} with proxy ${proxy.host}:${proxy.port}`);
      } else {
        failed++;
        console.log(`Failed ${profileName}: ${result.msg}`);
      }
    } catch (error) {
      failed++;
      console.log(`Error ${profileName}: ${error.message}`);
    }

    // Rate limiting - 1 second between requests
    await sleep(1000);
  }

  console.log(`\nDone! Created: ${created}, Failed: ${failed}`);
}

main().catch(console.error);
