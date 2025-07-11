from datetime import datetime

def generate_html_report(results, output_file, scan_info=None):
    """生成HTML报告"""
    
    # 计算统计信息
    total = len(results)
    success = sum(1 for r in results if r["status"] == "成功")
    failed = total - success
    
    # 按状态码分组
    status_groups = {}
    for result in results:
        if result["status_code"]:
            group = f"{result['status_code']} ({result['status_code']//100}xx)"
            if group not in status_groups:
                status_groups[group] = 0
            status_groups[group] += 1
    
    # 生成状态码统计HTML
    status_stats = ""
    for group, count in sorted(status_groups.items()):
        status_stats += f"<span class='stat-item'>{group}: {count}</span> "
    
    # 当前时间
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # HTML模板 - 使用三重引号和替换变量
    html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IP访问结果报告</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: #fff;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 20px;
        }}
        h1, h2, h3 {{
            color: #2c3e50;
        }}
        .summary {{
            background-color: #e1f5fe;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 20px;
        }}
        .stats {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-bottom: 15px;
        }}
        .stat-box {{
            background-color: #f8f9fa;
            border-radius: 6px;
            padding: 10px 15px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            min-width: 120px;
        }}
        .stat-item {{
            background-color: #e9ecef;
            padding: 4px 8px;
            border-radius: 4px;
            margin-right: 5px;
            display: inline-block;
            margin-bottom: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            font-size: 14px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #f2f2f2;
            position: sticky;
            top: 0;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .success {{
            background-color: #e8f5e9;
        }}
        .fail {{
            background-color: #ffebee;
        }}
        .status-200 {{ background-color: #e8f5e9; }}
        .status-300 {{ background-color: #e1f5fe; }}
        .status-400 {{ background-color: #fff8e1; }}
        .status-500 {{ background-color: #ffebee; }}
        .search-box {{
            padding: 10px 0;
            margin-bottom: 20px;
        }}
        #search {{
            padding: 8px 12px;
            width: 300px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }}
        .url {{
            word-break: break-all;
        }}
        .footer {{
            margin-top: 30px;
            text-align: center;
            font-size: 12px;
            color: #777;
        }}
        @media print {{
            body {{
                padding: 0;
                background-color: white;
            }}
            .container {{
                box-shadow: none;
                padding: 0;
            }}
            .no-print {{
                display: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>IP访问结果报告</h1>
        
        <div class="summary">
            <h3>扫描信息</h3>
            <p><strong>扫描时间:</strong> {current_time}</p>
            {f'<p><strong>扫描参数:</strong> {scan_info}</p>' if scan_info else ''}
        </div>
        
        <div class="stats">
            <div class="stat-box">
                <h3>总体统计</h3>
                <p>总URL数: <strong>{total}</strong></p>
                <p>成功: <strong>{success}</strong></p>
                <p>失败: <strong>{failed}</strong></p>
            </div>
            
            <div class="stat-box">
                <h3>状态码分布</h3>
                <div>
                    {status_stats}
                </div>
            </div>
        </div>
        
        <div class="search-box no-print">
            <input type="text" id="search" placeholder="搜索URL、状态码或IP...">
        </div>
        
        <table id="results-table">
            <thead>
                <tr>
                    <th>序号</th>
                    <th>URL</th>
                    <th>IP:端口</th>
                    <th>状态码</th>
                    <th>响应大小</th>
                    <th>响应时间</th>
                    <th>页面标题</th>
                </tr>
            </thead>
            <tbody>
"""
    
    # 添加表格行
    for i, result in enumerate(results, 1):
        status_class = ""
        if result["status_code"]:
            status_class = f"status-{result['status_code'] // 100}00"
        elif result["status"] == "失败":
            status_class = "fail"
        
        title = result.get("title", "") or ""
        title = title.replace('"', '&quot;')
        
        html_template += f"""                <tr class="{status_class}">
                    <td>{i}</td>
                    <td class="url"><a href="{result['url']}" target="_blank">{result['url']}</a></td>
                    <td>{result['ip_port']}</td>
                    <td>{result['status_code'] or '连接失败'}</td>
                    <td>{result['response_size']} 字节</td>
                    <td>{result['time']} ms</td>
                    <td title="{title}">{title[:50]}{('...' if len(title) > 50 else '')}</td>
                </tr>
"""
    
    # 结束HTML
    html_template += """            </tbody>
        </table>
        
        <div class="footer">
            <p>生成于 """ + current_time + """ | 使用IP批量访问脚本</p>
        </div>
    </div>
    
    <script>
        document.getElementById('search').addEventListener('keyup', function() {
            const value = this.value.toLowerCase();
            const rows = document.querySelectorAll('#results-table tbody tr');
            
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(value) ? '' : 'none';
            });
        });
    </script>
</body>
</html>
"""
    
    # 写入文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    return True