import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os
from datetime import datetime

st.title("🏃‍♂️ 運動・健康記録アプリ")
st.caption("運動・体重・気分を記録")

CSV_FILE = "health_log.csv"


st.header("📋 今日の記録を入力")

with st.form(key="health_form"):
    日付 = st.date_input("日付", value=datetime.today())
    運動の種類 = st.selectbox("運動の種類", ["ウォーキング", "ランニング", "ヨガ", "筋トレ", "ストレッチ", "サイクリング", "その他"])
    運動時間 = st.number_input("運動時間（分）", min_value=0, max_value=300, value=30)
    体重 = st.number_input("体重（kg）", min_value=30.0, max_value=200.0, value=55.0, step=0.1)
    気分スコア = st.slider("気分スコア（1〜5）", min_value=1, max_value=5, value=3)

    submitted = st.form_submit_button("✅ 記録を保存")

    if submitted:
        new_record = {
            "日付": 日付.strftime("%Y-%m-%d"),
            "運動の種類": 運動の種類,
            "運動時間": 運動時間,
            "体重": 体重,
            "気分スコア": 気分スコア
        }

        if os.path.exists(CSV_FILE):
            df_existing = pd.read_csv(CSV_FILE)
            df_existing = df_existing[df_existing["日付"] != new_record["日付"]]
            df_updated = pd.concat([df_existing, pd.DataFrame([new_record])], ignore_index=True)
        else:
            df_updated = pd.DataFrame([new_record])

        df_updated = df_updated.sort_values("日付")
        df_updated.to_csv(CSV_FILE, index=False)
        st.cache_data.clear()  # ← キャッシュを手動でクリア
        st.success(f"✅ {new_record['日付']} の記録を保存しました！")


if os.path.exists(CSV_FILE):
    st.markdown("---")
    st.header("📈 分析ダッシュボード")

    @st.cache_data
    def load_data():
        df = pd.read_csv(CSV_FILE)
        df["日付"] = pd.to_datetime(df["日付"])
        df = df.sort_values("日付")
        return df

    df = load_data()

    # 目標の設定
    st.sidebar.header("🎯 目標設定")
    目標_体重 = st.sidebar.number_input("目標体重 (kg)", value=55.0)
    目標_運動時間 = st.sidebar.number_input("1日あたりの目標運動時間 (分)", value=30)

    # 表示範囲フィルタ
    st.sidebar.header("📅 表示範囲")
    min_date = df["日付"].min()
    max_date = df["日付"].max()
    date_range = st.sidebar.date_input("表示期間", [min_date, max_date])

    filtered_df = df[(df["日付"] >= pd.to_datetime(date_range[0])) & (df["日付"] <= pd.to_datetime(date_range[1]))]

    if not filtered_df.empty:
        # メトリクス表示
        col1, col2, col3 = st.columns(3)
        latest_weight = filtered_df["体重"].iloc[-1]
        avg_exercise = filtered_df["運動時間"].mean()
        goal_weight_achieved = latest_weight <= 目標_体重
        goal_exercise_achieved = avg_exercise >= 目標_運動時間

        with col1:
            st.metric("現在の体重", f"{latest_weight:.1f} kg", delta=f"{latest_weight - 目標_体重:+.1f} kg")
        with col2:
            st.metric("平均運動時間", f"{avg_exercise:.1f} 分", delta=f"{avg_exercise - 目標_運動時間:+.1f} 分")
        with col3:
            achieved = "達成済 🎉" if goal_weight_achieved and goal_exercise_achieved else "未達成"
            st.metric("目標達成状況", achieved)

        #  運動時間と体重の2軸グラフ
        st.subheader("📈 運動時間と体重の推移")
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(
            x=filtered_df["日付"],
            y=filtered_df["体重"],
            mode="lines+markers",
            name="体重 (kg)",
            yaxis="y1"
        ))
        fig1.add_trace(go.Bar(
            x=filtered_df["日付"],
            y=filtered_df["運動時間"],
            name="運動時間 (分)",
            yaxis="y2",
            opacity=0.6,
            marker_color="lightskyblue"
        ))
        fig1.update_layout(
            yaxis=dict(title="体重 (kg)", side="left"),
            yaxis2=dict(title="運動時間 (分)", overlaying="y", side="right"),
            xaxis=dict(title="日付"),
            legend=dict(x=0.01, y=0.99),
            height=400
        )
        st.plotly_chart(fig1, use_container_width=True)

        # 体重変化トレンド
        st.subheader("📉 体重の変化トレンド")
        fig2 = px.line(
            filtered_df,
            x="日付",
            y="体重",
            title="体重の変化トレンド",
            markers=True
        )
        st.plotly_chart(fig2, use_container_width=True)

        # 気分スコアの分布
        if "気分スコア" in filtered_df.columns:
            st.subheader("😊 気分スコアの傾向")
            fig3 = px.histogram(
                filtered_df,
                x="気分スコア",
                nbins=5,
                title="気分スコアの分布"
            )
            st.plotly_chart(fig3, use_container_width=True)

        # データの確認
        with st.expander("📄 データの確認"):
            st.dataframe(filtered_df)
    else:
        st.info("⚠️ 表示期間に該当するデータがありません。")
else:
    st.warning("📂 まだ記録が存在しません。まずは記録を入力してください。")
