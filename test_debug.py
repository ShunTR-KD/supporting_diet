#!/usr/bin/env python3
# test_debug.py - 開発用JSONデータ表示機能のテスト

import os
import sys
sys.path.append('/app')

# 環境変数設定
from dotenv import load_dotenv
load_dotenv()

import utils as ut

def main():
    """開発用テストの実行"""
    print("=" * 60)
    print("NutriBuddy 開発用JSONデータ表示テスト")
    print("=" * 60)
    
    # 楽天APIキーの確認
    rakuten_app_id = os.getenv("RAKUTEN_APPLICATION_ID")
    if not rakuten_app_id:
        print("❌ RAKUTEN_APPLICATION_ID が設定されていません")
        return
    
    print(f"✅ 楽天API ID: {rakuten_app_id[:8]}...")
    
    try:
        # デバッグモード有効化
        ut.set_debug_mode(True)
        print("デバッグモード有効")
        
        # 1. カテゴリ一覧取得テスト
        print("\n" + "=" * 40)
        print("1. カテゴリ一覧取得テスト")
        print("=" * 40)
        
        categories = ut.fetch_rakuten_categories(rakuten_app_id)
        if categories:
            print("✅ カテゴリ一覧取得成功")
            ut.debug_display_json_data(categories, "楽天レシピカテゴリ一覧")
        else:
            print("❌ カテゴリ一覧取得失敗")
        
        # 2. レシピ取得テスト（和食）
        print("\n" + "=" * 40)
        print("2. レシピ取得テスト（和食）")
        print("=" * 40)
        
        recipes = ut.fetch_top_recipes_by_genre("和食", rakuten_app_id)
        if recipes:
            print(f"✅ 和食レシピ取得成功: {len(recipes)}件")
            if recipes:
                ut.debug_display_json_data(recipes[:2], "和食レシピサンプル（最初の2件）")
        else:
            print("❌ 和食レシピ取得失敗")
        
        # 3. 包括的なテスト実行
        print("\n" + "=" * 40)
        print("3. 包括的APIテスト")
        print("=" * 40)
        
        ut.run_debug_tests(rakuten_app_id)
        
    except Exception as e:
        print(f"❌ テスト実行エラー: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("テスト完了 - ログファイル logs/ で詳細を確認してください")
    print("=" * 60)

if __name__ == "__main__":
    main()