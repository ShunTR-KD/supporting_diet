# main.py
import streamlit as st
from datetime import date
import logging

from initialize import initialize_once
import components as cp
import constants as ct
import utils as ut

# ログ設定の初期化
ut.setup_logging()
logger = logging.getLogger(__name__)

st.set_page_config(page_title="NutriBuddy", page_icon=ct.MEAL_ICONS, layout="wide")

# 初回のみ初期化
logger.info("=== NutriBuddy アプリケーション開始 ===")
initialize_once()
env = ut.load_env()
OPENAI_API_KEY = env["OPENAI_API_KEY"]
RAKUTEN_APP_ID = env["RAKUTEN_APPLICATION_ID"]
DB_PATH = env["SQLITE_PATH"]

logger.info("環境変数読み込み完了")

# ヘッダ
st.title(f"{ct.MEAL_ICONS} NutriBuddy（ニュートリバディ）")
st.caption("「あなたの努力を見守り、毎日応援してくれる管理栄養士ダイエットパートナーAI」")
st.info("💡 「レシピ提案」を押せば、あなたにピッタリの料理を提案できます！")
st.caption("回答は必ずしも正しいとは限りません。重要な情報は確認するようにしてください。")

# 今日の摂取カロリー計算（サイドバー表示前に実行）
logger.info("今日の摂取カロリー計算開始")
consumed = ut.sum_today_kcal(DB_PATH)

# サイドバー入力（摂取済みカロリーを渡す）
inputs = cp.sidebar_inputs({
    "target_kcal": ct.DEFAULT_TARGET_KCAL,
    "meal_budget": ct.DEFAULT_MEAL_BUDGET_JPY,
    "meal_kcal": ct.DEFAULT_MEAL_KCAL,
    "location": ct.DEFAULT_LOCATION
}, consumed)

# 目標カロリーが設定された後に残りカロリーを計算
remaining = ut.calc_remaining_kcal(inputs["target_kcal"], consumed)

logger.info(f"ユーザー設定 - 目標カロリー: {inputs['target_kcal']}kcal, 予算: {inputs['meal_budget']}円, 場所: {inputs['location']}")
logger.info(f"摂取済み: {consumed:.1f}kcal, 残り: {remaining:.1f}kcal")

# 食事記録後の更新確認
if "meal_recorded" in st.session_state:
    if st.session_state.meal_recorded:
        added_kcal = st.session_state.get("last_added_kcal", 0)
        st.success(f"食事を記録しました！{added_kcal:.0f}kcal追加 - カロリーが更新されました。")
        st.session_state.meal_recorded = False

# 開発者モード（デバッグ用）
with st.sidebar.expander("🔧 開発者モード", expanded=False):
    st.write("**楽天APIデバッグ機能**")
    
    if st.button("カテゴリ一覧取得", help="楽天レシピAPIのカテゴリ一覧を取得してログに表示"):
        if RAKUTEN_APP_ID:
            with st.spinner("カテゴリ一覧を取得中..."):
                try:
                    ut.debug_fetch_and_display_categories(RAKUTEN_APP_ID)
                    st.success("✅ カテゴリ一覧を取得しました。ログファイルを確認してください。")
                except Exception as e:
                    st.error(f"❌ カテゴリ取得エラー: {str(e)}")
        else:
            st.warning("RAKUTEN_APPLICATION_IDが設定されていません")
    
    if st.button("API テスト実行", help="楽天レシピAPIの包括的なテストを実行"):
        if RAKUTEN_APP_ID:
            with st.spinner("APIテストを実行中..."):
                try:
                    ut.run_debug_tests(RAKUTEN_APP_ID)
                    st.success("✅ APIテストが完了しました。ログファイルで詳細を確認できます。")
                except Exception as e:
                    st.error(f"❌ APIテストエラー: {str(e)}")
        else:
            st.warning("RAKUTEN_APPLICATION_IDが設定されていません")
    
    debug_mode = st.checkbox("デバッグモード", help="詳細なログ出力を有効にします")
    if debug_mode:
        ut.set_debug_mode(True)
        st.info("デバッグモードが有効です")
    else:
        ut.set_debug_mode(False)
    
    st.write("**ログファイル情報**")
    from datetime import datetime
    log_file = f"logs/nutribuddy_{datetime.now().strftime('%Y%m%d')}.log"
    st.code(f"ログファイル: {log_file}")

# 天気情報の表示制御
show_weather = st.button("🌤️ 天気情報を表示", key="toggle_weather")
if show_weather or st.session_state.get("weather_visible", False):
    # ボタンが押された場合は状態を更新
    if show_weather:
        st.session_state.weather_visible = not st.session_state.get("weather_visible", False)
    
    # 天気情報が表示状態の場合
    if st.session_state.get("weather_visible", False):
        with st.expander("🌤️ 今週の天気情報", expanded=True):
            # 非表示ボタンを追加
            if st.button("❌ 天気情報を非表示", key="hide_weather"):
                st.session_state.weather_visible = False
                st.rerun()
            
            logger.info("天気情報取得開始")
            weather = ut.fetch_weekly_weather(inputs["location"])
            cp.show_weather_calendar(weather)
    else:
        # 非表示の場合は簡易的な天気取得（体感温度のみ）
        logger.info("体感温度計算用の天気情報取得")
        weather = ut.fetch_weekly_weather(inputs["location"])
else:
    # 初回または非表示状態では簡易的な天気取得
    logger.info("体感温度計算用の天気情報取得")
    weather = ut.fetch_weekly_weather(inputs["location"])

# 今日の温度感（今日の最高気温を採用）
today_feel = "快適"
try:
    max_list = weather.get("daily", {}).get("temperature_2m_max", [])
    if max_list:
        today_feel = ut.temp_to_feel(float(max_list[0]))
        logger.info(f"今日の体感温度: {today_feel}")
except Exception as e:
    logger.warning(f"体感温度計算エラー: {str(e)}")

# デバッグ情報表示（開発用）
# with st.expander("🔧 デバッグ情報", expanded=False):
#     st.write(f"データベースパス: {DB_PATH}")
#     st.write(f"今日の日付: {date.today().isoformat()}")
#     st.write(f"摂取済みカロリー: {consumed:.1f}kcal")
#     st.write(f"目標カロリー: {inputs['target_kcal']}kcal")
#     st.write(f"残りカロリー: {remaining:.1f}kcal")

# st.metric(label="今日の残り摂取可能カロリー", value=f"{int(remaining)} kcal", delta=f"摂取済み {int(consumed)} kcal")
# logger.info(f"摂取済み: {consumed:.1f}kcal, 残り: {remaining:.1f}kcal")

# レシピ提案状態の管理
if inputs["propose"]:
    st.session_state.show_recipes = True
    st.session_state.current_genre = inputs["genre"]
    st.session_state.current_difficulty = inputs["difficulty"]
    st.session_state.current_meal_type = inputs["meal_type"]
    st.session_state.current_budget = inputs["meal_budget"]

# レシピ提案表示（セッション状態で管理）
if st.session_state.get("show_recipes", False):
    genre = st.session_state.get("current_genre", inputs["genre"])
    difficulty = st.session_state.get("current_difficulty", inputs["difficulty"])
    meal_type = st.session_state.get("current_meal_type", inputs["meal_type"])
    budget = st.session_state.get("current_budget", inputs["meal_budget"])
    
    logger.info(f"レシピ提案表示 - ジャンル: {genre}")
    proposal_mode = inputs.get("proposal_mode", ct.DEFAULT_PROPOSAL_MODE)
    
    if proposal_mode == "主食+副菜提案":
        st.subheader(f"{ct.RECIPE_ICONS} 主食+副菜 組み合わせ提案")
    else:
        st.subheader(f"{ct.RECIPE_ICONS} レシピ提案（上位4件×推定カロリー/PFC）")
    
    # クリアボタンを追加
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("レシピを非表示", key="clear_recipes"):
            st.session_state.show_recipes = False
            st.rerun()
    
    season = ut.get_season()
    
    # 動的カテゴリ検索を使用
    keyword = inputs.get("search_keyword")
    search_mode = inputs.get("search_mode", "ジャンル優先")
    
    # 検索パラメータの決定
    if search_mode == "キーワード優先" and keyword:
        # キーワード重視の検索
        recipes = ut.fetch_top_recipes_by_genre(keyword, RAKUTEN_APP_ID, keyword)
        logger.info(f"キーワード優先検索: '{keyword}'")
    else:
        # ジャンル優先の検索（従来通り）
        recipes = ut.fetch_top_recipes_by_genre(genre, RAKUTEN_APP_ID, keyword)
        logger.info(f"ジャンル優先検索: '{genre}'" + (f" + キーワード: '{keyword}'" if keyword else ""))

    if not recipes:
        logger.warning("レシピ取得失敗")
        st.warning("レシピが取得できませんでした。ジャンルやAPI設定を確認してください。")
    else:
        logger.info(f"レシピ取得成功 - {len(recipes)}件")
        # バッチ処理でパフォーマンス向上
        if len(recipes) > 1:
            logger.info("複数レシピの並行処理開始")
            with st.status("複数のレシピを並行処理中...", expanded=False) as status:
                kcal_infos = ut.batch_estimate_recipes_sync(recipes, 
                    difficulty=difficulty,
                    budget_jpy=budget,
                    season=season,
                    feel=today_feel
                )
                logger.info("並行処理完了")
                
                # カロリーフィルタリング処理
                meal_kcal_limit = inputs["meal_kcal"]
                filtered_recipes = []
                filtered_kcal_infos = []
                
                for i, (recipe, kcal_info) in enumerate(zip(recipes, kcal_infos)):
                    estimated_kcal = kcal_info.get('kcal', 0)
                    if estimated_kcal <= meal_kcal_limit + 100:  # 希望カロリー+100kcal以内
                        filtered_recipes.append(recipe)
                        filtered_kcal_infos.append(kcal_info)
                        logger.debug(f"レシピ承認: {recipe.get('recipeName', '')} ({estimated_kcal:.0f}kcal <= {meal_kcal_limit + 100}kcal)")
                    else:
                        logger.debug(f"レシピ除外: {recipe.get('recipeName', '')} ({estimated_kcal:.0f}kcal > {meal_kcal_limit + 100}kcal)")
                
                # フィルタリング後のレシピ数をチェック
                if len(filtered_recipes) >= 2:
                    recipes = filtered_recipes
                    kcal_infos = filtered_kcal_infos
                    logger.info(f"カロリーフィルタリング完了 - 表示レシピ: {len(recipes)}件")
                    status.update(label="カロリー条件に合うメニューを選定しました！", state="complete")
                else:
                    logger.warning(f"フィルタリング後のレシピが少数({len(filtered_recipes)}件) - 元のレシピを表示")
                    status.update(label="以下がおすすめのメニューです！", state="complete")
                    if len(filtered_recipes) > 0:
                        st.info(f"💡 希望カロリー({meal_kcal_limit}kcal)に完全に合うレシピは{len(filtered_recipes)}件でした。参考として他のレシピも表示します。")
        else:
            st.info("以下がおすすめのメニューです！")
            kcal_infos = []
        
        # 提案モードによる分岐処理
        if proposal_mode == "主食+副菜提案":
            # 複数レシピ組み合わせモード
            logger.info("主食+副菜提案モード開始")
            
            # より多くのレシピを取得（組み合わせ用）
            additional_recipes = []
            side_keywords = ["サラダ", "野菜", "副菜", "おかず"]
            
            for keyword in side_keywords:
                extra_recipes = ut.fetch_top_recipes_by_genre(keyword, RAKUTEN_APP_ID, keyword)
                if extra_recipes:
                    additional_recipes.extend(extra_recipes[:2])  # 各キーワードから2件
            
            # 既存レシピと追加レシピを結合
            all_recipes = recipes + additional_recipes
            
            # 追加レシピのカロリー推定
            if additional_recipes:
                logger.info(f"追加レシピ{len(additional_recipes)}件のカロリー推定開始")
                additional_kcal_infos = ut.batch_estimate_recipes_sync(additional_recipes,
                    difficulty=difficulty,
                    budget_jpy=budget,
                    season=season,
                    feel=today_feel
                )
                all_kcal_infos = kcal_infos + additional_kcal_infos
            else:
                all_kcal_infos = kcal_infos
            
            # 組み合わせ検索
            combinations = ut.find_recipe_combinations(all_recipes, all_kcal_infos, meal_kcal_limit)
            
            if combinations:
                logger.info(f"組み合わせ提案: {len(combinations)}件")
                for i, combo in enumerate(combinations, start=1):
                    # 組み合わせの応援メッセージ生成
                    combo_summary = f"{combo['combination_name']} / 合計{int(combo['total_kcal'])}kcal / {combo['type']} / 目標{meal_kcal_limit}kcal"
                    cheer = ut.generate_cheer(combo_summary)
                    
                    # 組み合わせカード表示
                    cp.recipe_combination_card(i, combo, cheer)
                    
                    # 記録ボタン（組み合わせ用）
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        button_key = f"log_combo_{i}_{combo['type']}"
                        if st.button(f"この組み合わせを{meal_type}に記録", key=button_key):
                            logger.info(f"🔥 組み合わせ記録ボタンクリック - {combo['combination_name']}, 合計カロリー: {combo['total_kcal']}")
                            try:
                                # 各レシピを個別に記録
                                for recipe_info in combo['recipes']:
                                    recipe_name = recipe_info['recipe'].get('recipeName', '')
                                    recipe_kcal = recipe_info['kcal_info'].get('kcal', 0)
                                    ut.insert_meal_log(DB_PATH, meal_type, recipe_name, float(recipe_kcal))
                                
                                # セッション状態で記録完了をマーク
                                st.session_state.meal_recorded = True
                                st.session_state.last_added_kcal = float(combo['total_kcal'])
                                
                                st.rerun()
                                
                            except Exception as e:
                                logger.error(f"組み合わせ記録エラー: {str(e)}")
                                st.error("食事記録に失敗しました。")
                    
                    st.divider()
            else:
                st.warning("適切な組み合わせが見つかりませんでした。1品提案モードをお試しください。")
        
        else:
            # 従来の1品提案モード
            logger.info("1品提案モード")
            
            for i, r in enumerate(recipes, start=1):
                recipe_name = r.get("recipeName", "")
                logger.debug(f"レシピ{i}表示処理: {recipe_name}")
                
                if i-1 < len(kcal_infos):
                    kcal_info = kcal_infos[i-1]
                else:
                    # フォールバック: 個別処理
                    logger.info(f"レシピ{i}の個別カロリー推定開始")
                    ingredients_str = ",".join(r.get("recipeMaterial", []))
                    kcal_info = ut.cached_estimate_recipe_kcal_pfc(
                        recipe_name=recipe_name,
                        ingredients_str=ingredients_str,
                        method=r.get("recipeIndication") or "",
                        difficulty=difficulty,
                        budget_jpy=budget,
                        season=season,
                        feel=today_feel
                    )
                
                # カロリー条件チェック（個別処理時）
                estimated_kcal = kcal_info.get('kcal', 0)
                meal_kcal_limit = inputs["meal_kcal"]
                is_over_calorie = estimated_kcal > meal_kcal_limit + 100
                
                summary = f"{recipe_name} / 約{int(kcal_info['kcal'])}kcal / {genre} / {difficulty} / 予算{budget}円 / 体感:{today_feel}"
                cheer = ut.generate_cheer(summary)
                
                # カロリーオーバー時の表示調整
                if is_over_calorie:
                    st.warning(f"⚠️ このレシピは希望カロリー({meal_kcal_limit}kcal)を{int(estimated_kcal - meal_kcal_limit)}kcal超過しています")
                
                cp.recipe_card(i, r, kcal_info, cheer)

                # 記録ボタン
                col1, col2 = st.columns([1,4])
                with col1:
                    button_key = f"log_{i}_{recipe_name[:10]}"  # より一意なキー
                    logger.debug(f"ボタン表示 - キー: {button_key}")
                    
                    if st.button(f"この料理を{meal_type}に記録", key=button_key):
                        logger.info(f"🔥 食事記録ボタンクリック - レシピ: {recipe_name}, カロリー: {kcal_info['kcal']}")
                        try:
                            # デバッグ: 挿入前の状態確認
                            before_consumed = ut.sum_today_kcal(DB_PATH)
                            logger.info(f"挿入前摂取カロリー: {before_consumed}kcal")
                            
                            # レコード挿入
                            ut.insert_meal_log(DB_PATH, meal_type, recipe_name, float(kcal_info["kcal"]))
                            
                            # デバッグ: 挿入後の状態確認
                            after_consumed = ut.sum_today_kcal(DB_PATH)
                            logger.info(f"挿入後摂取カロリー: {after_consumed}kcal")
                            
                            # セッション状態で記録完了をマーク
                            st.session_state.meal_recorded = True
                            st.session_state.last_added_kcal = float(kcal_info["kcal"])
                            
                            # ページを再実行して残カロリーを更新
                            logger.info("ページ再実行開始")
                            st.rerun()
                            
                        except Exception as e:
                            logger.error(f"食事記録エラー: {str(e)}")
                            import traceback
                            logger.error(f"エラー詳細: {traceback.format_exc()}")
                            st.error("食事記録に失敗しました。")
                st.divider()

# 1週間の献立
if inputs["weekly"]:
    logger.info("週間献立作成開始")
    
    # 週間献立でも動的検索を使用
    keyword = inputs.get("search_keyword")
    search_mode = inputs.get("search_mode", "ジャンル優先")
    
    if search_mode == "キーワード優先" and keyword:
        recipes = ut.fetch_top_recipes_by_genre(keyword, RAKUTEN_APP_ID, keyword)
    else:
        recipes = ut.fetch_top_recipes_by_genre(inputs["genre"], RAKUTEN_APP_ID, keyword)
    
    if recipes:
        logger.info(f"週間献立用レシピ取得: {len(recipes)}件")
        
        with st.status("1週間の献立を作成中...", expanded=False) as status:
            rows = []
            season = ut.get_season()
            
            # シンプルに同じ上位候補から日替わりで1品ずつ（本実装では重複回避や多様性ロジックを向上）
            for d in range(7):
                day_num = d + 1
                r = recipes[d % len(recipes)]
                recipe_name = r.get("recipeName", "")
                logger.debug(f"Day{day_num}の献立処理: {recipe_name}")
                
                ingredients_str = ",".join(r.get("recipeMaterial", []))
                kcal_info = ut.cached_estimate_recipe_kcal_pfc(
                    recipe_name=recipe_name,
                    ingredients_str=ingredients_str,
                    method=r.get("recipeIndication") or "",
                    difficulty=inputs["difficulty"],
                    budget_jpy=inputs["meal_budget"],
                    season=season,
                    feel=today_feel
                )
                summary = f"{recipe_name} / 約{int(kcal_info['kcal'])}kcal / 日{day_num}"
                cheer = ut.generate_cheer(summary)
                rows.append({
                    "日": f"Day {day_num}",
                    "料理名": recipe_name,
                    "推定kcal": int(kcal_info["kcal"]),
                    "レシピリンク": r.get("recipeUrl", ""),
                    "応援": cheer
                })
            
            logger.info("週間献立作成完了")
            status.update(label="1週間の献立を作成しました！", state="complete")
        
        cp.weekly_table(rows)
    else:
        logger.warning("週間献立作成失敗 - レシピ取得エラー")
        st.warning("献立を作成できませんでした（レシピ取得失敗）。")

logger.info("=== NutriBuddy アプリケーション処理完了 ===")
