// 安心散策－全齡友善地圖：伺服器端帳號密碼驗證（HTTP Basic Auth）
// 帳號密碼放在 Cloudflare 的 Secret：DEMO_USER、DEMO_PASS（不寫在程式碼裡）
// 沒設定 Secret 時一律拒絕（fail closed）

const enc = new TextEncoder();
const TODAYWORK = "https://tpnco.blob.core.windows.net/blobfs/Todaywork.json"; // 臺北市今日施工資訊（data.taipei 資料集 c208dabd…）

async function sameSecret(a, b) {
  // 先各自雜湊成固定長度，再做常數時間比較，避免從回應時間推測密碼
  const [ha, hb] = await Promise.all([
    crypto.subtle.digest("SHA-256", enc.encode(a)),
    crypto.subtle.digest("SHA-256", enc.encode(b)),
  ]);
  return crypto.subtle.timingSafeEqual(ha, hb);
}

function decodeBasic(header) {
  if (!header || !header.startsWith("Basic ")) return null;
  try {
    const bin = atob(header.slice(6).trim());
    const text = new TextDecoder().decode(Uint8Array.from(bin, (c) => c.charCodeAt(0)));
    const i = text.indexOf(":");
    return i < 0 ? null : [text.slice(0, i), text.slice(i + 1)];
  } catch {
    return null;
  }
}

const text = (body, status, extra = {}) =>
  new Response(body, {
    status,
    headers: { "content-type": "text/plain; charset=utf-8", "cache-control": "no-store", ...extra },
  });

export default {
  async fetch(request, env) {
    if (!env.DEMO_USER || !env.DEMO_PASS) {
      return text("網站尚未設定帳號密碼，暫不開放。", 503);
    }
    const cred = decodeBasic(request.headers.get("Authorization"));
    const ok =
      cred &&
      (await sameSecret(cred[0], env.DEMO_USER)) &
      (await sameSecret(cred[1], env.DEMO_PASS));
    if (!ok) {
      return text("請輸入帳號密碼。", 401, {
        "WWW-Authenticate": 'Basic realm="silver-safe-walk", charset="UTF-8"',
      });
    }
    const url = new URL(request.url);
    let res;
    if (url.pathname === "/api/todaywork") {
      // 臺北市今日施工資訊（新工處）：由本站轉送，Cloudflare 快取 10 分鐘；不解析內容，只原樣轉送
      try {
        const up = await fetch(TODAYWORK, { cf: { cacheTtl: 600, cacheEverything: true } });
        if (!up.ok) return text("施工資料暫時無法取得。", 502);
        res = new Response(up.body, { status: 200, headers: { "content-type": "application/json; charset=utf-8" } });
      } catch {
        return text("施工資料暫時無法取得。", 502);
      }
    } else {
      res = await env.ASSETS.fetch(request);
    }
    const out = new Response(res.body, res);
    out.headers.set("cache-control", url.pathname.startsWith("/api/") ? "private, max-age=600" : "no-store, private");
    out.headers.set("X-Robots-Tag", "noindex, nofollow");
    out.headers.set("X-Content-Type-Options", "nosniff");
    out.headers.set("Referrer-Policy", "no-referrer");
    out.headers.set("X-Frame-Options", "DENY");
    return out;
  },
};
