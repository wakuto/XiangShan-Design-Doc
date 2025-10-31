#!/usr/bin/env python3
"""
中国語版と日本語版のドキュメントの整合性をチェックするスクリプト
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

def get_file_stats(file_path: Path) -> Dict:
    """ファイルの統計情報を取得"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')
    
    # 基本統計
    stats = {
        'lines': len(lines),
        'chars': len(content),
        'non_empty_lines': len([l for l in lines if l.strip()]),
    }
    
    # Markdown要素のカウント
    stats['headers'] = len(re.findall(r'^#+\s', content, re.MULTILINE))
    stats['code_blocks'] = len(re.findall(r'```', content))
    stats['images'] = len(re.findall(r'!\[.*?\]\(.*?\)', content))
    stats['links'] = len(re.findall(r'\[.*?\]\(.*?\)', content)) - stats['images']
    stats['tables'] = len(re.findall(r'^\|', content, re.MULTILINE))
    
    return stats

def compare_files(zh_file: Path, ja_file: Path) -> Dict:
    """2つのファイルを比較"""
    zh_stats = get_file_stats(zh_file)
    ja_stats = get_file_stats(ja_file)
    
    issues = []
    
    # 行数の大きな差異をチェック（30%以上の差）
    if zh_stats['lines'] > 0:
        line_diff_percent = abs(zh_stats['lines'] - ja_stats['lines']) / zh_stats['lines'] * 100
        if line_diff_percent > 30:
            issues.append(f"行数の差が大きい: zh={zh_stats['lines']}, ja={ja_stats['lines']} ({line_diff_percent:.1f}%)")
    
    # 見出しの数が一致しているかチェック
    if zh_stats['headers'] != ja_stats['headers']:
        issues.append(f"見出し数が異なる: zh={zh_stats['headers']}, ja={ja_stats['headers']}")
    
    # コードブロックの数が一致しているかチェック
    if zh_stats['code_blocks'] != ja_stats['code_blocks']:
        issues.append(f"コードブロック数が異なる: zh={zh_stats['code_blocks']}, ja={ja_stats['code_blocks']}")
    
    # 画像の数が一致しているかチェック
    if zh_stats['images'] != ja_stats['images']:
        issues.append(f"画像数が異なる: zh={zh_stats['images']}, ja={ja_stats['images']}")
    
    return {
        'zh_stats': zh_stats,
        'ja_stats': ja_stats,
        'issues': issues
    }

def main():
    base_dir = Path(__file__).parent
    zh_dir = base_dir / 'docs' / 'zh'
    ja_dir = base_dir / 'docs' / 'ja'
    
    # 全ファイルを取得（.index.mdを除外）
    zh_files = sorted([f.relative_to(zh_dir) for f in zh_dir.rglob('*.md') if f.name != '.index.md'])
    
    problems = []
    ok_files = []
    
    print("=" * 80)
    print("中国語版と日本語版のドキュメント整合性チェック")
    print("=" * 80)
    print()
    
    for rel_path in zh_files:
        zh_file = zh_dir / rel_path
        ja_file = ja_dir / rel_path
        
        if not ja_file.exists():
            problems.append((str(rel_path), ["日本語版ファイルが存在しません"]))
            continue
        
        result = compare_files(zh_file, ja_file)
        
        if result['issues']:
            problems.append((str(rel_path), result['issues']))
        else:
            ok_files.append(str(rel_path))
    
    # 結果表示
    if problems:
        print(f"⚠️  問題が見つかったファイル: {len(problems)}件")
        print("=" * 80)
        for file_path, issues in problems:
            print(f"\n📄 {file_path}")
            for issue in issues:
                print(f"   - {issue}")
    
    print()
    print("=" * 80)
    print(f"✅ 問題なし: {len(ok_files)}件")
    print(f"⚠️  要確認: {len(problems)}件")
    print(f"📊 合計: {len(zh_files)}件")
    print("=" * 80)
    
    # 詳細ログをファイルに出力
    with open(base_dir / 'translation_check_log.txt', 'w', encoding='utf-8') as f:
        f.write("翻訳整合性チェック結果\n")
        f.write("=" * 80 + "\n\n")
        
        if problems:
            f.write("【問題が見つかったファイル】\n\n")
            for file_path, issues in problems:
                f.write(f"{file_path}\n")
                for issue in issues:
                    f.write(f"  - {issue}\n")
                f.write("\n")
        
        f.write("\n【問題なしのファイル】\n\n")
        for file_path in ok_files:
            f.write(f"{file_path}\n")
    
    print(f"\n詳細ログを translation_check_log.txt に出力しました")

if __name__ == '__main__':
    main()
