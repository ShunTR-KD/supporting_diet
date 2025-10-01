#!/usr/bin/env python3
# debug_categories.py - カテゴリ構造の詳細確認

import os
import sys
sys.path.append('/app')

from dotenv import load_dotenv
load_dotenv()

import utils as ut
import json

def inspect_categories():
    """カテゴリAPIの実際のレスポンス構造を確認"""
    app_id = os.getenv("RAKUTEN_APPLICATION_ID")
    if not app_id:
        print("❌ RAKUTEN_APPLICATION_ID が設定されていません")
        return
    
    print("📋 楽天レシピカテゴリAPI レスポンス構造確認")
    print("=" * 60)
    
    try:
        # カテゴリ取得
        categories_data = ut.fetch_rakuten_categories(app_id)
        
        if not categories_data:
            print("❌ カテゴリデータの取得に失敗")
            return
        
        print(f"✅ データ取得成功")
        print(f"📊 データサイズ: {len(str(categories_data))} bytes")
        print(f"📁 トップレベルキー: {list(categories_data.keys())}")
        
        if 'result' in categories_data:
            result = categories_data['result']
            print(f"📈 result の型: {type(result)}")
            print(f"📈 result の長さ: {len(result) if hasattr(result, '__len__') else 'N/A'}")
            
            if isinstance(result, list) and result:
                print(f"📋 最初の要素の型: {type(result[0])}")
                print(f"📋 最初の要素のキー: {list(result[0].keys()) if isinstance(result[0], dict) else 'N/A'}")
                print(f"📋 最初の要素の内容（一部）:")
                if isinstance(result[0], dict):
                    for key, value in list(result[0].items())[:5]:
                        print(f"   {key}: {str(value)[:100]}{'...' if len(str(value)) > 100 else ''}")
                        
                # カテゴリ一覧の表示
                print("\n📝 カテゴリ一覧（最初の20件）:")
                display_count = min(20, len(result))
                for i in range(display_count):
                    category = result[i]
                    if isinstance(category, dict):
                        cat_id = category.get('categoryId', 'N/A')
                        cat_name = category.get('categoryName', 'N/A')
                        parent_id = category.get('parentCategoryId', 'N/A')
                        print(f"   {i+1:3d}. ID: {cat_id:>6} | 親ID: {parent_id:>6} | 名前: {cat_name}")
                    else:
                        print(f"   {i+1:3d}. [非辞書型データ]: {type(category)} = {str(category)[:50]}")
                
                if len(result) > 20:
                    print(f"   ... 他 {len(result)-20} 件")
                    
            elif isinstance(result, dict):
                print(f"📋 result は辞書型です:")
                for key, value in list(result.items())[:10]:
                    print(f"   {key}: {type(value)} = {str(value)[:100]}{'...' if len(str(value)) > 100 else ''}")
            else:
                print(f"📋 result の型が予期しない形式: {type(result)}")
                print(f"   内容: {str(result)[:200]}...")
        else:
            print("❌ 'result' キーが見つかりません")
            print(f"利用可能なキー: {list(categories_data.keys())}")
            
    except Exception as e:
        print(f"❌ エラー: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    inspect_categories()