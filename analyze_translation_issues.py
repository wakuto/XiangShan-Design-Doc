#!/usr/bin/env python3
"""
翻訳の問題を詳細に分析し、重要度別に分類するスクリプト
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict

def get_file_stats(file_path: Path) -> Dict:
    """ファイルの統計情報を取得"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')
    
    stats = {
        'lines': len(lines),
        'chars': len(content),
        'non_empty_lines': len([l for l in lines if l.strip()]),
        'headers': len(re.findall(r'^#+\s', content, re.MULTILINE)),
        'code_blocks': len(re.findall(r'```', content)),
        'images': len(re.findall(r'!\[.*?\]\(.*?\)', content)),
        'links': len(re.findall(r'\[.*?\]\(.*?\)', content)),
        'tables': len(re.findall(r'^\|', content, re.MULTILINE)),
    }
    
    return stats

def classify_severity(zh_stats: Dict, ja_stats: Dict) -> str:
    """問題の重要度を分類"""
    if zh_stats['lines'] == 0:
        return "empty"
    
    line_diff_percent = abs(zh_stats['lines'] - ja_stats['lines']) / zh_stats['lines'] * 100
    
    # 重大: 80%以上の行数差
    if line_diff_percent >= 80:
        return "critical"
    # 高: 50%以上の行数差
    elif line_diff_percent >= 50:
        return "high"
    # 中: 30%以上の行数差、または見出し・画像・コードブロックの大きな不一致
    elif line_diff_percent >= 30 or \
         abs(zh_stats['headers'] - ja_stats['headers']) >= 5 or \
         abs(zh_stats['images'] - ja_stats['images']) >= 3 or \
         abs(zh_stats['code_blocks'] - ja_stats['code_blocks']) >= 2:
        return "medium"
    # 低: わずかな不一致
    elif line_diff_percent >= 10 or \
         zh_stats['headers'] != ja_stats['headers'] or \
         zh_stats['images'] != ja_stats['images'] or \
         zh_stats['code_blocks'] != ja_stats['code_blocks']:
        return "low"
    
    return "ok"

def main():
    base_dir = Path(__file__).parent
    zh_dir = base_dir / 'docs' / 'zh'
    ja_dir = base_dir / 'docs' / 'ja'
    
    # 全ファイルを取得（.index.mdを除外）
    zh_files = sorted([f.relative_to(zh_dir) for f in zh_dir.rglob('*.md') if f.name != '.index.md'])
    
    # 重要度別に分類
    issues_by_severity = defaultdict(list)
    
    for rel_path in zh_files:
        zh_file = zh_dir / rel_path
        ja_file = ja_dir / rel_path
        
        if not ja_file.exists():
            issues_by_severity['missing'].append({
                'file': str(rel_path),
                'issue': '日本語版ファイルが存在しません'
            })
            continue
        
        zh_stats = get_file_stats(zh_file)
        ja_stats = get_file_stats(ja_file)
        severity = classify_severity(zh_stats, ja_stats)
        
        if severity != "ok":
            line_diff_percent = abs(zh_stats['lines'] - ja_stats['lines']) / zh_stats['lines'] * 100 if zh_stats['lines'] > 0 else 0
            
            issues_by_severity[severity].append({
                'file': str(rel_path),
                'zh_lines': zh_stats['lines'],
                'ja_lines': ja_stats['lines'],
                'line_diff_percent': line_diff_percent,
                'zh_headers': zh_stats['headers'],
                'ja_headers': ja_stats['headers'],
                'zh_images': zh_stats['images'],
                'ja_images': ja_stats['images'],
                'zh_code_blocks': zh_stats['code_blocks'],
                'ja_code_blocks': ja_stats['code_blocks'],
            })
    
    # レポート作成
    print("=" * 100)
    print("翻訳整合性チェック - 詳細分析レポート")
    print("=" * 100)
    print()
    
    total_files = len(zh_files)
    total_issues = sum(len(v) for k, v in issues_by_severity.items() if k != 'ok')
    ok_files = total_files - total_issues
    
    print(f"📊 総ファイル数: {total_files}")
    print(f"✅ 問題なし: {ok_files}")
    print(f"⚠️  問題あり: {total_issues}")
    print()
    
    # 重要度別の統計
    severity_names = {
        'critical': '🔴 重大（80%以上の翻訳不足）',
        'high': '🟠 高（50-80%の翻訳不足）',
        'medium': '🟡 中（30-50%の翻訳不足または構造的不一致）',
        'low': '🟢 低（軽微な不一致）',
        'missing': '⚫ ファイル不存在'
    }
    
    for severity in ['critical', 'high', 'medium', 'low', 'missing']:
        if severity in issues_by_severity and issues_by_severity[severity]:
            print(f"\n{severity_names[severity]}: {len(issues_by_severity[severity])}件")
            print("-" * 100)
    
    # 詳細レポートをファイルに出力
    with open(base_dir / 'translation_analysis_report.md', 'w', encoding='utf-8') as f:
        f.write("# 翻訳整合性チェック - 詳細分析レポート\n\n")
        f.write(f"- 総ファイル数: {total_files}\n")
        f.write(f"- 問題なし: {ok_files}\n")
        f.write(f"- 問題あり: {total_issues}\n\n")
        
        for severity in ['critical', 'high', 'medium', 'low', 'missing']:
            if severity in issues_by_severity and issues_by_severity[severity]:
                f.write(f"\n## {severity_names[severity]} ({len(issues_by_severity[severity])}件)\n\n")
                
                if severity == 'missing':
                    for item in issues_by_severity[severity]:
                        f.write(f"- `{item['file']}`: {item['issue']}\n")
                else:
                    # 行数差でソート
                    sorted_items = sorted(issues_by_severity[severity], 
                                         key=lambda x: x['line_diff_percent'], 
                                         reverse=True)
                    
                    f.write("| ファイル | 中国語版行数 | 日本語版行数 | 差異率 | 見出し数(zh/ja) | 画像数(zh/ja) | コードブロック(zh/ja) |\n")
                    f.write("|---------|------------|------------|--------|----------------|--------------|--------------------|\n")
                    
                    for item in sorted_items:
                        f.write(f"| `{item['file']}` | {item['zh_lines']} | {item['ja_lines']} | "
                               f"{item['line_diff_percent']:.1f}% | "
                               f"{item['zh_headers']}/{item['ja_headers']} | "
                               f"{item['zh_images']}/{item['ja_images']} | "
                               f"{item['zh_code_blocks']}/{item['ja_code_blocks']} |\n")
        
        # 推奨対応策
        f.write("\n## 推奨対応策\n\n")
        
        if 'critical' in issues_by_severity and issues_by_severity['critical']:
            f.write("### 🔴 重大問題への対応\n\n")
            f.write("以下のファイルは翻訳がほとんど完了していません（80%以上の内容が未翻訳）。優先的に対応が必要です：\n\n")
            for item in sorted(issues_by_severity['critical'], key=lambda x: x['line_diff_percent'], reverse=True)[:10]:
                f.write(f"1. `{item['file']}` - {item['line_diff_percent']:.1f}%未翻訳（{item['zh_lines']}行中{item['zh_lines']-item['ja_lines']}行が未翻訳）\n")
        
        if 'high' in issues_by_severity and issues_by_severity['high']:
            f.write("\n### 🟠 高優先度問題への対応\n\n")
            f.write("以下のファイルは翻訳が半分程度しか完了していません。早急な対応が推奨されます：\n\n")
            for item in sorted(issues_by_severity['high'], key=lambda x: x['line_diff_percent'], reverse=True):
                f.write(f"- `{item['file']}` - {item['line_diff_percent']:.1f}%未翻訳\n")
        
        if 'medium' in issues_by_severity and issues_by_severity['medium']:
            f.write("\n### 🟡 中優先度問題への対応\n\n")
            f.write("以下のファイルは部分的に翻訳が不完全、または構造的な不一致があります：\n\n")
            for item in issues_by_severity['medium']:
                f.write(f"- `{item['file']}`\n")
        
        f.write("\n## カテゴリ別分析\n\n")
        
        # カテゴリ別の統計
        category_stats = defaultdict(lambda: {'total': 0, 'issues': 0})
        
        for rel_path in zh_files:
            parts = Path(rel_path).parts
            category = parts[0] if parts else 'root'
            category_stats[category]['total'] += 1
            
            # 問題があるかチェック
            ja_file = ja_dir / rel_path
            if ja_file.exists():
                zh_file = zh_dir / rel_path
                zh_stats = get_file_stats(zh_file)
                ja_stats = get_file_stats(ja_file)
                severity = classify_severity(zh_stats, ja_stats)
                if severity != 'ok':
                    category_stats[category]['issues'] += 1
            else:
                category_stats[category]['issues'] += 1
        
        f.write("| カテゴリ | 総ファイル数 | 問題ファイル数 | 完了率 |\n")
        f.write("|---------|------------|--------------|--------|\n")
        
        for category in sorted(category_stats.keys()):
            stats = category_stats[category]
            completion_rate = (stats['total'] - stats['issues']) / stats['total'] * 100
            f.write(f"| {category} | {stats['total']} | {stats['issues']} | {completion_rate:.1f}% |\n")
    
    print("\n✅ 詳細分析レポートを translation_analysis_report.md に出力しました")
    print()
    
    # サマリー表示
    print("=" * 100)
    print("【重要度別サマリー】")
    print("=" * 100)
    
    for severity in ['critical', 'high', 'medium', 'low']:
        if severity in issues_by_severity and issues_by_severity[severity]:
            print(f"\n{severity_names[severity]}")
            for item in issues_by_severity[severity][:5]:  # 各カテゴリ最大5件表示
                print(f"  - {item['file']} ({item['line_diff_percent']:.1f}%差異)")
            if len(issues_by_severity[severity]) > 5:
                print(f"  ... 他{len(issues_by_severity[severity])-5}件")

if __name__ == '__main__':
    main()
