const fs = require('fs');
const http = require('http');

const ADSPOWER_API = 'http://local.adspower.net:50325';
const GROUP_ID = '8671133';

// Read proxies
const proxies = fs.readFileSync('./downloads/webshare_proxies_2500.txt', 'utf8')
  .trim()
  .split('\n')
  .map(line => {
    const [host, port, user, pass] = line.split(':');
    return { host, port, user, pass };
  });

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
      headers: { 'Content-Type': 'application/json' }
    };
    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try { resolve(JSON.parse(data)); }
        catch (e) { resolve(data); }
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

async function getProfilesToDelete() {
  const response = await makeRequest(`${ADSPOWER_API}/api/v1/user/list?page_size=500`);
  const profiles = response.data.list.filter(p => {
    const match = p.name.match(/^tt(\d+)$/);
    if (!match) return false;
    const num = parseInt(match[1]);
    return num >= START_PROFILE && num <= END_PROFILE;
  });
  return profiles.map(p => p.user_id);
}

async function deleteProfile(userId) {
  const url = `${ADSPOWER_API}/api/v1/user/delete`;
  return await makeRequest(url, 'POST', { user_ids: [userId] });
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
      language: ['en-US', 'en'],
      ua: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
  };
  return await makeRequest(url, 'POST', body);
}

async function main() {
  // Step 1: Delete existing profiles
  console.log('Getting profiles to delete...');
  const userIds = await getProfilesToDelete();
  console.log(`Found ${userIds.length} profiles to delete`);

  for (let i = 0; i < userIds.length; i++) {
    const result = await deleteProfile(userIds[i]);
    console.log(`Deleted ${i + 1}/${userIds.length}: ${result.code === 0 ? 'OK' : result.msg}`);
    await sleep(500);
  }

  console.log('\nWaiting 3 seconds...\n');
  await sleep(3000);

  // Step 2: Recreate profiles with macOS
  console.log(`Creating profiles tt${START_PROFILE} to tt${END_PROFILE} with macOS...`);

  let created = 0;
  let failed = 0;

  for (let i = START_PROFILE; i <= END_PROFILE; i++) {
    const profileName = `tt${i}`;
    const proxy = proxies[i - 1];

    if (!proxy) {
      console.log(`No proxy for ${profileName}`);
      failed++;
      continue;
    }

    const result = await createProfile(profileName, proxy);
    if (result.code === 0) {
      created++;
      console.log(`[${created}/250] Created ${profileName} (macOS)`);
    } else {
      failed++;
      console.log(`Failed ${profileName}: ${result.msg}`);
    }
    await sleep(1000);
  }

  console.log(`\nDone! Created: ${created}, Failed: ${failed}`);
}

main().catch(console.error);
