# 走這條！求最大陰影面積（互動原型）

「這里需要你」長出的第一個解方：長輩用 App 導航，白天找陰涼、晚上找安全，設計重點是數位安全（不當低頭族、不用手機也能用）。市政 debug松 概念原型。白天避曬、清晨與晚上自動切換安全優先；廁所、飲水機與長者行人事故點位取自政府開放資料，路線、遮蔭、路燈、天氣為模擬。

- 網頁：`public/index.html`（單一檔案，不需建置）
- 母體「這里需要你」：獨立專案 [hd2026-bit/zheli-needs-you](https://github.com/hd2026-bit/zheli-needs-you)；網站版放在這裡的 `public/zheli/index.html`（從該專案的 `public/index.html` 複製），網址加 `/zheli/`
- 驗證：`src/worker.js`，所有請求先檢查帳號密碼才回傳網頁（伺服器端 HTTP Basic Auth）
- 分析程式：`analysis/`，用開放資料重現所有數字（見 `analysis/README.md`）
- 版本：每一版都是一筆 commit，可隨時回到舊版；版本內容見 `CHANGELOG.md`

## 部署：Cloudflare Workers（免費、不需綁卡）
- 網址：`https://silver-safe-walk.TBD.workers.dev`
- GitHub 推送到 `main` 後，Cloudflare 會自動重新部署

### 設定／更換帳號密碼
1. Cloudflare → Workers & Pages → silver-safe-walk → **Settings**，在頁面**最上方**的 **Variables and Secrets** 按 **+ Add**
   （出現「Add environment variable」視窗才是對的）
   ⚠️ 不要設在 **Builds** 卡片裡的 Variables and secrets，那是建置用的，網站讀不到
2. 環境勾 **Production**，新增兩列並各自勾 **Secret**：
   - `DEMO_USER`：帳號
   - `DEMO_PASS`：密碼（建議 12 字以上）
3. 按 **Add variable and deploy**
- 換密碼：同一處把 `DEMO_PASS` 改掉即可
- 沒設定時網站一律回「暫不開放」（503），不會意外公開
- 要取消某人的權限：更換 `DEMO_PASS`，再把新密碼告訴其他人

### 回到舊版
- Cloudflare：Deployments 分頁 → 選舊的部署 → Rollback
- GitHub：`git revert` 或用舊 commit 的 `public/index.html` 覆蓋後推送

## 平板 Demo
- iPad：設定 → 輔助使用 → 朗讀內容 → 聲音 → 中文（台灣），下載加強版語音
- Android：Google 文字轉語音下載「中文（台灣）」
- 瀏覽器開啟後「加入主畫面」可全螢幕；開場前先按一次 🔊 暖機
- 接藍牙喇叭或會場音響；關閉自動鎖定、開勿擾

## 兩種入口
- **Demo**：網址直接開，有「⚙ 控制」可切換時段、燈號（黑客松展示用）
- **正式入口**：網址後面加 `?app`，或「加入主畫面」後從圖示開啟。沒有控制面板，日夜依手機時間自動切換；字級與提醒設定記在這支手機上
