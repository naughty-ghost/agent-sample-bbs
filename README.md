# agent-sample-bbs
Copilot coding agentを利用して作成されています

## 掲示板アプリケーション

このプロジェクトは掲示板（Bulletin Board System）の開発環境です。

### 技術スタック
- Python 3.12 + Flask LTS
- PostgreSQL 15.10  
- Docker + Docker Compose

### 環境の起動方法

```bash
# Docker Composeで環境を起動
docker compose up

# または、バックグラウンドで起動
docker compose up -d
```

### アクセス方法
- アプリケーション: http://localhost:5000
- PostgreSQL: localhost:5432

### 環境の停止方法

```bash
docker compose down
```

### 開発環境
推奨エディター: Visual Studio Code
