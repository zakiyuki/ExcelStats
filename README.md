# 人口データ可視化システム

Excelファイルから人口データを読み込み、年齢階級別の人口分布グラフを作成するFlaskアプリケーションです。

## 機能

- Excelファイル（.xlsx）のアップロード
- 人口データのデータベース保存
- 年齢階級別人口分布の棒グラフ作成
- レスポンシブなWebインターフェース

## 必要な環境

- Python 3.8以上
- MySQL 5.7以上
- pip（Pythonパッケージマネージャー）

## インストール

1. リポジトリをクローンまたはダウンロード
```bash
git clone <repository-url>
cd Flask
```

2. 仮想環境を作成（推奨）
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

3. 依存関係をインストール
```bash
pip install -r requirements.txt
```

## データベース設定

1. MySQLデータベースを作成
```sql
CREATE DATABASE mydatabase CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

2. `dbAccessor.py`の接続情報を更新
```python
USER_NAME = "your_username"
PASSWORD = "your_password"
HOST = "localhost:3306"
DATABASE = "mydatabase"
```

## 使用方法

1. アプリケーションを起動
```bash
python app.py
```

2. ブラウザで `http://localhost:5000` にアクセス

3. Excelファイルをアップロード
   - 「総人口」の行を含むExcelファイルを選択
   - ファイル形式は.xlsxのみ対応

4. グラフを作成・表示
   - アップロード完了後、「グラフを作成」ボタンをクリック
   - 作成されたグラフを表示

## ファイル構造

```
Flask/
├── app.py                 # メインアプリケーション
├── dbAccessor.py          # データベース接続設定
├── mydatabase.py          # データベースモデル
├── requirements.txt       # 依存関係
├── README.md             # このファイル
├── static/
│   ├── css/
│   │   └── style.css     # スタイルシート
│   └── img/              # 生成されたグラフ画像
└── templates/
    ├── index.html        # ホームページ
    ├── upload.html       # アップロードページ
    ├── create.html       # グラフ作成完了ページ
    └── display.html      # グラフ表示ページ
```

## データ形式

Excelファイルは以下の形式である必要があります：
- 2列目に「総人口」の文字列を含む行
- 4列目：年齢階級
- 7列目：総人口数
- 8列目：男性人口数
- 9列目：女性人口数

## トラブルシューティング

### データベース接続エラー
- MySQLサーバーが起動しているか確認
- 接続情報（ユーザー名、パスワード、ホスト）が正しいか確認

### ファイルアップロードエラー
- ファイル形式が.xlsxか確認
- ファイルサイズが大きすぎないか確認
- Excelファイルの形式が正しいか確認

### グラフ作成エラー
- データベースにデータが保存されているか確認
- 静的ファイルディレクトリの書き込み権限を確認

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。





