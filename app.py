# -*- coding: utf-8 -*-
import os
import logging
import hashlib
from io import BytesIO
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import japanize_matplotlib
import re

from flask import Flask, render_template, request, flash, redirect, url_for
from dbAccessor import session
from mydatabase import Files, Dataset

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # セッション管理用

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 静的ファイルのディレクトリを確認
STATIC_IMG_DIR = os.path.join(app.static_folder, 'img')
os.makedirs(STATIC_IMG_DIR, exist_ok=True)


def compute_file_hash(file_storage) -> str:
    """アップロードされたファイルの内容ハッシュ(SHA256)を計算"""
    data = file_storage.read()
    digest = hashlib.sha256(data).hexdigest()
    # pandasで再読込できるよう先頭に戻す
    file_storage.stream.seek(0)
    return digest


def get_latest_dataset_id():
    latest = session.query(Dataset).order_by(Dataset.created_at.desc()).first()
    return latest.id if latest else None


def get_data_from_db(dataset_id: int | None = None):
    """データベースから指定データセットのデータを取得してDataFrameに変換。
    dataset_id未指定時は最新データセットを使用。
    """
    if dataset_id is None:
        dataset_id = get_latest_dataset_id()
    if dataset_id is None:
        return None

    db_records = session.query(Files).filter(Files.dataset_id == dataset_id).order_by(Files.id.asc()).all()
    if not db_records:
        return None
    data_list = []
    for row in db_records:
        data_list.append({
            "age": row.age,
            "total": row.total,
            "male": row.male,
            "female": row.female
        })
    df = pd.DataFrame(data_list)
    df['total'] = pd.to_numeric(df['total'], errors='coerce').fillna(0).astype(int)
    df['male'] = pd.to_numeric(df['male'], errors='coerce').fillna(0).astype(int)
    df['female'] = pd.to_numeric(df['female'], errors='coerce').fillna(0).astype(int)
    return df


def preprocess_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """年齢階級で重複する行を集約し、自然な年齢順に並べ替える"""
    if df is None or df.empty:
        return df
    # 年齢で集約（合計）
    grouped = (
        df.groupby('age', as_index=False)
          .agg({'total': 'sum', 'male': 'sum', 'female': 'sum'})
    )

    def extract_age_start(age_str: str) -> int:
        if not isinstance(age_str, str):
            return 10**9
        # 先頭の数字を抽出（例: "0～4歳" -> 0, "85歳以上" -> 85）
        m = re.search(r"(\d+)", age_str)
        return int(m.group(1)) if m else 10**9

    grouped['sort_key'] = grouped['age'].apply(extract_age_start)
    grouped = grouped.sort_values(['sort_key', 'age']).drop(columns=['sort_key']).reset_index(drop=True)
    return grouped


def save_graph(plt, filename):
    """グラフを保存してメモリを解放"""
    graph_path = os.path.join(STATIC_IMG_DIR, filename)
    plt.savefig(graph_path, format='svg', bbox_inches='tight', dpi=300)
    plt.close()
    logger.info(f"グラフを保存しました: {graph_path}")
    return filename


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/datasets", methods=["GET"])
def datasets():
    """登録済みデータセット一覧を表示"""
    ds_list = session.query(Dataset).order_by(Dataset.created_at.desc()).all()
    # 件数取得
    counts = {}
    for ds in ds_list:
        cnt = session.query(Files).filter(Files.dataset_id == ds.id).count()
        counts[ds.id] = cnt
    return render_template("datasets.html", datasets=ds_list, counts=counts)


@app.route("/upload", methods=["GET", "POST"])
def upload():
    """Excelファイルをアップロードしてデータセットを更新/新規作成"""
    if request.method == "GET":
        return render_template("upload.html")
    
    if "fileInput" not in request.files:
        flash("ファイルが選択されていません", "error")
        return redirect(url_for('upload'))
    
    file_input = request.files["fileInput"]
    if file_input.filename == "":
        flash("ファイルが選択されていません", "error")
        return redirect(url_for('upload'))
    
    if not file_input.filename.endswith('.xlsx'):
        flash("Excelファイル（.xlsx）を選択してください", "error")
        return redirect(url_for('upload'))
    
    try:
        # ファイルハッシュで同一判定
        file_hash = compute_file_hash(file_input)
        logger.info(f"アップロードファイルのハッシュ: {file_hash}")

        # Excelを読み込み
        df = pd.read_excel(file_input, engine="openpyxl")
        logger.info(f"Excelファイルを読み込みました: {len(df)}行")

        # ローカルセッションでトランザクション管理
        db = session()
        try:
            existing_ds = db.query(Dataset).filter(Dataset.file_hash == file_hash).first()

            if existing_ds:
                # 一致する場合は当該データセットを丸ごと更新
                logger.info(f"既存データセット更新: id={existing_ds.id}")
                # 既存行削除
                db.query(Files).filter(Files.dataset_id == existing_ds.id).delete(synchronize_session=False)
                target_dataset_id = existing_ds.id
            else:
                # 異なる場合は新規データセット作成
                new_ds = Dataset(file_hash=file_hash, name=os.path.basename(file_input.filename))
                db.add(new_ds)
                db.flush()  # new_ds.id 取得
                logger.info(f"新規データセット作成: id={new_ds.id}")
                target_dataset_id = new_ds.id

            # 行の挿入
            saved_count = 0
            for v in df.values:
                if len(v) > 8 and v[1] == "総人口":
                    files = Files(
                        time_code=str(v[0]) if pd.notna(v[0]) else "",
                        age=str(v[3]) if pd.notna(v[3]) else "",
                        total=int(v[6]) if pd.notna(v[6]) else 0,
                        male=int(v[7]) if pd.notna(v[7]) else 0,
                        female=int(v[8]) if pd.notna(v[8]) else 0,
                        dataset_id=target_dataset_id,
                    )
                    db.add(files)
                    saved_count += 1

            db.commit()
            action = "更新" if existing_ds else "作成"
            flash(f"データセットを{action}しました（{saved_count}件）", "success")
            return redirect(url_for('datasets'))
        except Exception as e:
            logger.error(f"データセット保存エラー: {e}")
            db.rollback()
            flash(f"データセットの保存中にエラーが発生しました: {str(e)}", "error")
            return redirect(url_for('upload'))
        finally:
            db.close()
    except Exception as e:
        logger.error(f"ファイル処理エラー: {e}")
        flash(f"ファイルの処理中にエラーが発生しました: {str(e)}", "error")
        return redirect(url_for('upload'))


@app.route("/create", methods=["POST"])
def create():
    """男女別グラフを作成（データセット選択対応）"""
    try:
        dataset_id = request.form.get('dataset_id', type=int)
        df = get_data_from_db(dataset_id)
        if df is None:
            flash("データが見つかりません。まずファイルをアップロードしてください。", "error")
            return redirect(url_for('upload'))
        
        df = preprocess_dataframe(df)

        # グラフ作成
        plt.figure(figsize=(16, 10))
        x = df["age"]
        x_total, x_male, x_female = df["total"], df["male"], df["female"]
        bar_width = 0.3
        index = range(len(x))

        plt.bar([i - bar_width for i in index], x_total, width=bar_width, 
                label="男女計", color="#2E86AB", alpha=0.8, edgecolor='white', linewidth=1)
        plt.bar(index, x_male, width=bar_width, 
                label="男子", color="#A23B72", alpha=0.8, edgecolor='white', linewidth=1)
        plt.bar([i + bar_width for i in index], x_female, width=bar_width, 
                label="女子", color="#F18F01", alpha=0.8, edgecolor='white', linewidth=1)

        plt.xlabel("年齢階級", fontsize=16, fontweight='bold')
        plt.ylabel("人口（人）", fontsize=16, fontweight='bold')
        plt.title("年齢階級別の人口分布（男女計・男子・女子）", fontsize=20, fontweight='bold', pad=20)
        plt.xticks(index, x, rotation=45, ha='right', fontsize=12)
        plt.yticks(fontsize=12)
        plt.legend(fontsize=14, loc='upper right', framealpha=0.9)
        plt.grid(True, axis="y", linestyle="--", alpha=0.3)
        plt.tight_layout(pad=3.0)
        
        save_graph(plt, 'population.svg')
        flash("グラフを作成しました", "success")
        return render_template("create.html", population='population.svg')
    except Exception as e:
        logger.error(f"グラフ作成エラー: {e}")
        flash(f"グラフの作成中にエラーが発生しました: {str(e)}", "error")
        return redirect(url_for('upload'))


@app.route("/create_total", methods=["POST"])
def create_total():
    """総数だけのグラフを作成（データセット選択対応）"""
    try:
        dataset_id = request.form.get('dataset_id', type=int)
        df = get_data_from_db(dataset_id)
        if df is None:
            flash("データが見つかりません。まずファイルをアップロードしてください。", "error")
            return redirect(url_for('upload'))
        
        df = preprocess_dataframe(df)

        plt.figure(figsize=(16, 10))
        x = df["age"]
        x_total = df["total"]
        index = range(len(x))

        bars = plt.bar(index, x_total, width=0.6, color="#2E86AB", 
                      alpha=0.8, edgecolor='white', linewidth=2)
        for i, bar in enumerate(bars):
            bar.set_color(plt.cm.Blues(0.3 + 0.7 * i / len(bars)))

        plt.xlabel("年齢階級", fontsize=16, fontweight='bold')
        plt.ylabel("総人口（人）", fontsize=16, fontweight='bold')
        plt.title("年齢階級別の総人口分布", fontsize=20, fontweight='bold', pad=20)
        plt.xticks(index, x, rotation=45, ha='right', fontsize=12)
        plt.yticks(fontsize=12)
        plt.grid(True, axis="y", linestyle="--", alpha=0.3)
        plt.tight_layout(pad=3.0)
        
        for i, total in enumerate(x_total):
            if total > 0:
                plt.text(i, total + max(x_total) * 0.01, f'{total:,}', 
                        ha='center', va='bottom', fontsize=10, fontweight='bold',
                        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
        
        save_graph(plt, 'total_population.svg')
        flash("総数グラフを作成しました", "success")
        return render_template("create.html", population='total_population.svg', graph_type='total')
    except Exception as e:
        logger.error(f"総数グラフ作成エラー: {e}")
        flash(f"総数グラフの作成中にエラーが発生しました: {str(e)}", "error")
        return redirect(url_for('upload'))


@app.route("/display", methods=["POST"])
def display():
    """グラフを表示"""
    return render_template("display.html")


@app.route("/display_total", methods=["POST"])
def display_total():
    """総数グラフを表示"""
    return render_template("display.html", graph_type='total')


@app.route("/home", methods=["POST"])
def home():
    """ホームページに戻る"""
    return redirect(url_for('index'))


if __name__ == "__main__":
    app.run()