# Heniiii — 語言學習平台設計文件

## 概述

Heniiii 是一個語言學習平台，支援英文、日文、台語三種語言。核心功能包括分級學習課程、每日填字遊戲挑戰、自建單字卡（含間隔重複）、多維度排行榜、部落格文章系統，以及角色權限管理的後台。

## 技術棧

| 層級 | 技術 |
|---|---|
| 前端 | SvelteKit (TypeScript) |
| 後端 | FastAPI (Python) |
| 資料庫 | PostgreSQL |
| 快取/排行榜 | Redis |
| 部署 | Docker Compose，自架固定 IP 伺服器 |

## 系統架構

```
┌─────────────────────────────────────────────┐
│              Docker Compose                  │
│                                              │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐  │
│  │ SvelteKit│  │ FastAPI  │  │PostgreSQL │  │
│  │ :3000    │  │ :8000    │  │ :5432     │  │
│  │ 前台/後台│──│ API/Svc  │──│ DB        │  │
│  └──────────┘  └──────────┘  └───────────┘  │
│                     │                        │
│                ┌────┴─────┐                  │
│                │  Redis   │                  │
│                │  :6379   │                  │
│                └──────────┘                  │
└─────────────────────────────────────────────┘
```

- SvelteKit 負責前台與後台 UI，以 route group 區分
- FastAPI 統一處理所有 API，內部以 Service Layer 拆分業務邏輯
- Service Layer 設計乾淨邊界，未來可抽出為 MCP Server
- Redis 用於排行榜 Sorted Set、Session 快取、每日挑戰狀態

## 網址結構

### 前台 (SvelteKit)

```
/                           # 首頁
/login                      # 登入
/register                   # 註冊

/learn/{lang}               # 語言學習首頁 (en / ja / tailo)
/learn/{lang}/{level}       # 難度分級課程列表
/learn/{lang}/lesson/{id}   # 單一課程

/daily                      # 今日挑戰總覽
/daily/crossword            # 今日填字遊戲
/daily/crossword/archive    # 歷史題目

/flashcards                 # 我的單字卡列表
/flashcards/new             # 建立新卡組
/flashcards/{id}            # 卡組練習

/leaderboard                # 全站排行
/leaderboard/{lang}         # 語言排行
/leaderboard/daily          # 每日挑戰排行

/blog                       # 文章列表
/blog/{slug}                # 單篇文章

/search?q=...&lang=...      # 搜尋

/profile                    # 個人資料/學習統計
/profile/settings           # 帳號設定
```

### 後台

```
/admin                      # 儀表板
/admin/articles             # 文章管理
/admin/articles/new
/admin/articles/{id}/edit
/admin/lessons              # 課程管理
/admin/lessons/new
/admin/lessons/{id}/edit
/admin/crossword            # 填字遊戲管理
/admin/crossword/new
/admin/crossword/{id}/edit
/admin/vocabulary           # 單字庫管理
/admin/users                # 使用者管理（僅 admin）
/admin/roles                # 角色權限管理（僅 admin）
```

### API (FastAPI — api.heniiii.com)

```
POST   /auth/register
POST   /auth/login
POST   /auth/oauth/{provider}
POST   /auth/refresh
POST   /auth/logout

GET    /learn/{lang}/levels
GET    /learn/{lang}/lessons
GET    /learn/{lang}/lessons/{id}

GET    /daily/today
GET    /daily/crossword/{date}
POST   /daily/crossword/submit

GET    /flashcards
POST   /flashcards
PUT    /flashcards/{id}
DELETE /flashcards/{id}

GET    /leaderboard?scope=...&lang=...&period=...

GET    /blog
GET    /blog/{slug}

GET    /search?q=...&lang=...&type=...

POST   /admin/articles
PUT    /admin/articles/{id}
POST   /admin/crossword
GET    /admin/users
```

## 資料模型

### users

| 欄位 | 型別 | 說明 |
|---|---|---|
| id | UUID | PK |
| email | VARCHAR | 唯一 |
| password_hash | VARCHAR | nullable，OAuth 用戶無密碼 |
| display_name | VARCHAR | 顯示名稱 |
| avatar_url | VARCHAR | 頭像 |
| role | ENUM | admin / editor / user |
| oauth_provider | VARCHAR | google / line / github |
| oauth_id | VARCHAR | 第三方 ID |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

### languages

| 欄位 | 型別 | 說明 |
|---|---|---|
| id | SERIAL | PK |
| code | VARCHAR | en / ja / tailo |
| name_zh | VARCHAR | 英文 / 日文 / 台語 |
| display_system | VARCHAR | alphabet / kana_kanji / tailo_hanzi |

### difficulty_levels

| 欄位 | 型別 | 說明 |
|---|---|---|
| id | SERIAL | PK |
| language_id | FK | → languages |
| slug | VARCHAR | beginner, n5, basic... |
| label_zh | VARCHAR | 顯示名稱 |
| sort_order | INT | 排序 |

### lessons

| 欄位 | 型別 | 說明 |
|---|---|---|
| id | UUID | PK |
| language_id | FK | → languages |
| difficulty_id | FK | → difficulty_levels |
| title | VARCHAR | 標題 |
| content | JSONB | 多種內容區塊 |
| author_id | FK | → users |
| status | ENUM | draft / published |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

### vocabulary

| 欄位 | 型別 | 說明 |
|---|---|---|
| id | UUID | PK |
| language_id | FK | → languages |
| word | VARCHAR | 單字 |
| pronunciation | VARCHAR | 音標 / 假名 / 台羅 |
| meaning_zh | VARCHAR | 中文意思 |
| example_sentence | TEXT | 例句 |
| difficulty_id | FK | → difficulty_levels |
| audio_url | VARCHAR | nullable |

### flashcard_decks

| 欄位 | 型別 | 說明 |
|---|---|---|
| id | UUID | PK |
| user_id | FK | → users |
| title | VARCHAR | 卡組名稱 |
| language_id | FK | → languages |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

### flashcard_items

| 欄位 | 型別 | 說明 |
|---|---|---|
| id | UUID | PK |
| deck_id | FK | → flashcard_decks |
| front_text | VARCHAR | 正面 |
| back_text | VARCHAR | 背面 |
| pronunciation | VARCHAR | 發音 |
| familiarity | INT | 0-5，SM-2 用 |
| next_review_at | TIMESTAMP | 下次複習時間 |
| last_reviewed_at | TIMESTAMP | 上次複習時間 |

### crossword_puzzles

| 欄位 | 型別 | 說明 |
|---|---|---|
| id | UUID | PK |
| language_id | FK | → languages |
| publish_date | DATE | 唯一，每日一題 |
| grid_data | JSONB | 格子配置 |
| clues | JSONB | {across: [], down: []} |
| difficulty_id | FK | → difficulty_levels |
| created_by | FK | → users |
| status | ENUM | draft / scheduled / published |

### crossword_submissions

| 欄位 | 型別 | 說明 |
|---|---|---|
| id | UUID | PK |
| puzzle_id | FK | → crossword_puzzles |
| user_id | FK | → users |
| answers | JSONB | 使用者答案 |
| score | INT | 分數 |
| completed_at | TIMESTAMP | 完成時間 |
| time_spent_seconds | INT | 花費秒數 |
| created_at | TIMESTAMP | |

### articles

| 欄位 | 型別 | 說明 |
|---|---|---|
| id | UUID | PK |
| title | VARCHAR | 標題 |
| slug | VARCHAR | URL 用，唯一 |
| content | TEXT | Markdown |
| cover_image_url | VARCHAR | 封面圖 |
| author_id | FK | → users |
| language_id | FK | nullable，通用文章不綁語言 |
| tags | JSONB | 標籤陣列 |
| status | ENUM | draft / published |
| published_at | TIMESTAMP | |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

### user_progress

| 欄位 | 型別 | 說明 |
|---|---|---|
| id | UUID | PK |
| user_id | FK | → users |
| language_id | FK | → languages |
| lesson_id | FK | → lessons |
| score | INT | 分數 |
| completed_at | TIMESTAMP | |
| created_at | TIMESTAMP | |

### daily_scores

| 欄位 | 型別 | 說明 |
|---|---|---|
| id | UUID | PK |
| user_id | FK | → users |
| date | DATE | |
| language_id | FK | nullable |
| score_type | ENUM | lesson / crossword / total |
| score | INT | |
| streak_days | INT | 連續天數 |

## 核心功能設計

### 認證系統

- 帳密註冊：email + 密碼（bcrypt 雜湊）
- OAuth 登入：Google、LINE、GitHub，首次登入自動建立帳號
- JWT 雙 token：access token（15 分鐘）+ refresh token（7 天，存 Redis）
- 未登入可瀏覽首頁、部落格、排行榜；學習、單字卡、每日挑戰需登入

### 學習模組

- 語言各自獨立難度分級：英文（beginner / intermediate / advanced）、日文（N5-N1）、台語（basic / intermediate / advanced）
- 課程內容用 JSONB 儲存，支援區塊類型：文字說明、單字表、練習題、音檔
- 完成課程記錄分數到 user_progress，累計到排行榜

### 填字遊戲（Crossword）

- 後台建立題目：編輯器設定格子大小、填入單字、撰寫提示
- 排程發布：status 從 scheduled 自動轉 published
- 前端互動：點格子輸入字母/假名/台羅拼音，即時檢查交叉格
- 計時計分：完成時間越短分數越高
- 完成後顯示答案解析與相關單字學習連結

### 單字卡

- 使用者自建卡組，每張卡正面/背面自定義
- SM-2 間隔重複演算法：依熟悉度（0-5）排程複習時間
- 練習模式：翻卡、自評熟悉度，系統自動排下次複習
- 可從課程或字典一鍵加入單字卡

### 排行榜

- Redis Sorted Set 儲存即時排名
- 三種維度：全站總排行、各語言排行、每日挑戰排行
- 排名依據：總分、連續學習天數、填字完成速度
- 每日凌晨快照到 daily_scores 做歷史紀錄

### 搜尋

- PostgreSQL tsvector 全文搜尋，範圍：課程、單字、文章
- 篩選條件：語言、難度、內容類型
- 台語支援漢字與台羅拼音雙向匹配

### 台語特殊處理

- 台羅拼音為主要顯示，漢字輔助
- 填字遊戲用台羅拼音字母填入
- 搜尋同時支援台羅與漢字
- vocabulary 表 pronunciation 欄位存台羅拼音

## 後台管理

### 角色權限

| 權限 | admin | editor |
|---|---|---|
| 文章 CRUD | ✓ | ✓ |
| 課程 CRUD | ✓ | ✓ |
| 填字遊戲 CRUD | ✓ | ✓ |
| 單字庫管理 | ✓ | ✓ |
| 使用者管理 | ✓ | ✗ |
| 角色指派 | ✓ | ✗ |
| 儀表板統計 | ✓ | 只看自己的內容 |

### 儀表板

- 今日活躍使用者數、新註冊數
- 各語言學習人數分布
- 每日挑戰參與率
- 最近發布的文章/課程列表

## 專案結構

```
heniiii/
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── alembic/
│   │   └── versions/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── dependencies.py
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── lesson.py
│   │   │   ├── vocabulary.py
│   │   │   ├── crossword.py
│   │   │   ├── flashcard.py
│   │   │   ├── article.py
│   │   │   └── progress.py
│   │   ├── schemas/
│   │   │   ├── user.py
│   │   │   ├── lesson.py
│   │   │   └── ...
│   │   ├── services/
│   │   │   ├── auth_service.py
│   │   │   ├── learning_service.py
│   │   │   ├── game_service.py
│   │   │   ├── dictionary_service.py
│   │   │   ├── content_service.py
│   │   │   └── leaderboard_service.py
│   │   ├── routers/
│   │   │   ├── auth.py
│   │   │   ├── learn.py
│   │   │   ├── daily.py
│   │   │   ├── flashcards.py
│   │   │   ├── blog.py
│   │   │   ├── search.py
│   │   │   ├── leaderboard.py
│   │   │   └── admin/
│   │   │       ├── articles.py
│   │   │       ├── lessons.py
│   │   │       ├── crossword.py
│   │   │       └── users.py
│   │   └── utils/
│   │       ├── security.py
│   │       ├── sm2.py
│   │       └── crossword.py
│   └── tests/
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── svelte.config.js
│   ├── src/
│   │   ├── lib/
│   │   │   ├── components/
│   │   │   │   ├── CrosswordGrid.svelte
│   │   │   │   ├── FlashcardDeck.svelte
│   │   │   │   ├── Leaderboard.svelte
│   │   │   │   ├── LessonCard.svelte
│   │   │   │   └── SearchBar.svelte
│   │   │   ├── stores/
│   │   │   │   ├── auth.ts
│   │   │   │   └── user.ts
│   │   │   └── api/
│   │   │       └── client.ts
│   │   └── routes/
│   │       ├── +layout.svelte
│   │       ├── +page.svelte
│   │       ├── (auth)/
│   │       │   ├── login/
│   │       │   └── register/
│   │       ├── (app)/
│   │       │   ├── learn/[lang]/
│   │       │   ├── daily/
│   │       │   ├── flashcards/
│   │       │   ├── profile/
│   │       │   └── search/
│   │       ├── (public)/
│   │       │   ├── blog/
│   │       │   └── leaderboard/
│   │       └── (admin)/
│   │           └── admin/
│   └── static/
│       └── fonts/
└── docs/
    └── superpowers/
        └── specs/
```

## 未來 MCP 擴展方向

Service Layer 設計乾淨邊界，未來可抽出為 MCP Server：

| Service | MCP 用途 |
|---|---|
| content_service | AI 自動產出文章草稿、單字清單 |
| game_service | AI 生成填字遊戲題目 |
| learning_service | AI 分析弱點、推薦學習路徑 |
| dictionary_service | AI 助教查詢詞彙、例句、台羅發音 |

抽取方式：同一個 Service 方法同時被 FastAPI Router 和 MCP Tool handler 呼叫，不需改動業務邏輯。

## 視覺風格

- 簡約現代風格，大量留白、乾淨排版
- 類似 Duolingo 的清爽感
- 響應式設計，支援桌面與手機（通勤使用場景）
