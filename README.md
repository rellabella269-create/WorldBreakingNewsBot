# 🌍 World Breaking News Bot

A Telegram news automation bot that collects news from RSS feeds,
formats the stories, prevents duplicate posts, and automatically
publishes new stories to every Telegram channel registered by the admin.

## ✨ Features

- 🌍 World news collection
- 🚨 Automatic breaking-news publishing
- 📰 Multiple RSS sources
- 🔄 Duplicate prevention
- 📢 Supports 100+ Telegram channels
- ➕ Add channels directly through Telegram
- ❌ Remove channels directly through Telegram
- 🔴 Temporarily disable channels
- 🟢 Re-enable channels
- 📋 View all registered channels
- 🔔 Personal user alerts
- 🗃️ SQLite database
- ☁️ Railway compatible
- 🔐 Bot token kept in environment variables

## 📁 Files

```text
WorldBreakingNewsBot/
│
├── main.py
├── bot.py
├── config.py
├── database.py
├── news_fetcher.py
├── formatter.py
├── requirements.txt
├── runtime.txt
├── Procfile
├── Dockerfile
├── .gitignore
└── README.md
