#!/usr/bin/env python3
"""
Automated price analysis reporter - generates and emails comprehensive pricing insights
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List
import statistics
from price_analyzer import PriceAnalyzer
from email_sender import EmailSender

class PriceAnalysisReporter:
    def __init__(self):
        self.analyzer = PriceAnalyzer()
        self.email_sender = EmailSender()
        self.report_date = datetime.now()
        
    def generate_comprehensive_report(self) -> Dict:
        """Generate a comprehensive price analysis report"""
        
        if not self.analyzer.price_history:
            return {"error": "No price history data available"}
        
        report_data = {
            "report_date": self.report_date.strftime("%Y-%m-%d"),
            "report_period": self._determine_report_period(),
            "products": {},
            "summary": {}
        }
        
        all_products_analysis = []
        
        # Analyze each product
        for product_key, product_data in self.analyzer.price_history.items():
            analysis = self.analyzer.analyze_product_pricing(product_key)
            
            if "error" not in analysis:
                report_data["products"][product_key] = analysis
                all_products_analysis.append(analysis)
        
        # Generate summary insights
        if all_products_analysis:
            report_data["summary"] = self._generate_summary_insights(all_products_analysis)
        
        return report_data
    
    def _determine_report_period(self) -> str:
        """Determine what period this report covers"""
        month = self.report_date.month
        
        # Quarterly reports
        if month in [1, 4, 7, 10]:
            quarter_map = {1: "Q4", 4: "Q1", 7: "Q2", 10: "Q3"}
            prev_quarter = quarter_map[month]
            year = self.report_date.year if month != 1 else self.report_date.year - 1
            return f"{prev_quarter} {year} Quarterly Report"
        else:
            # Monthly reports
            prev_month = self.report_date.replace(day=1) - timedelta(days=1)
            return f"{prev_month.strftime('%B %Y')} Monthly Report"
    
    def _generate_summary_insights(self, analyses: List[Dict]) -> Dict:
        """Generate high-level insights across all products"""
        
        total_products = len(analyses)
        total_savings_potential = 0
        trending_up = 0
        trending_down = 0
        best_deals = []
        
        for analysis in analyses:
            stats = analysis['price_statistics']
            trends = analysis['trends']
            
            # Calculate total savings potential
            current = stats['current_price']
            lowest = stats['lowest_price']
            if current > lowest:
                total_savings_potential += (current - lowest)
            
            # Count trends
            if trends['trend'] == 'increasing':
                trending_up += 1
            elif trends['trend'] == 'decreasing':
                trending_down += 1
            
            # Collect best deals
            if analysis['best_deals']:
                latest_deal = analysis['best_deals'][0]
                best_deals.append({
                    'product': analysis['product_name'],
                    'price': latest_deal['price'],
                    'days_ago': latest_deal['days_ago']
                })
        
        # Sort best deals by recency
        best_deals.sort(key=lambda x: x['days_ago'])
        
        return {
            "total_products_tracked": total_products,
            "total_savings_potential": round(total_savings_potential, 2),
            "price_trends": {
                "increasing": trending_up,
                "decreasing": trending_down,
                "stable": total_products - trending_up - trending_down
            },
            "recent_best_deals": best_deals[:3],  # Top 3 recent deals
            "market_sentiment": self._determine_market_sentiment(trending_up, trending_down, total_products)
        }
    
    def _determine_market_sentiment(self, up: int, down: int, total: int) -> str:
        """Determine overall market sentiment"""
        if total == 0:
            return "unknown"
        
        up_pct = (up / total) * 100
        down_pct = (down / total) * 100
        
        if up_pct > 60:
            return "bullish"  # Prices generally rising
        elif down_pct > 60:
            return "bearish"  # Prices generally falling
        else:
            return "mixed"  # Mixed signals
    
    def format_html_report(self, report_data: Dict) -> str:
        """Format the report as beautiful HTML for email"""
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f7fa; }}
                .container {{ max-width: 800px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }}
                .header h1 {{ margin: 0; font-size: 28px; font-weight: 300; }}
                .header p {{ margin: 10px 0 0 0; opacity: 0.9; }}
                .summary {{ background: #f8f9fb; padding: 25px; border-bottom: 1px solid #e1e8ed; }}
                .summary h2 {{ color: #2c3e50; margin-top: 0; }}
                .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
                .stat-card {{ background: white; padding: 20px; border-radius: 8px; border-left: 4px solid #3498db; }}
                .stat-number {{ font-size: 24px; font-weight: bold; color: #2c3e50; }}
                .stat-label {{ color: #7f8c8d; font-size: 14px; }}
                .product {{ margin: 25px; padding: 20px; border: 1px solid #e1e8ed; border-radius: 8px; }}
                .product h3 {{ color: #2c3e50; margin-top: 0; }}
                .price-info {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin: 15px 0; }}
                .price-item {{ text-align: center; }}
                .price-value {{ font-size: 18px; font-weight: bold; }}
                .price-label {{ font-size: 12px; color: #7f8c8d; }}
                .trend {{ padding: 8px 16px; border-radius: 20px; font-size: 14px; font-weight: bold; }}
                .trend-up {{ background: #fee; color: #e74c3c; }}
                .trend-down {{ background: #efe; color: #27ae60; }}
                .trend-stable {{ background: #f0f0f0; color: #7f8c8d; }}
                .buy-btn {{ background: #3498db; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; margin-top: 15px; }}
                .footer {{ background: #2c3e50; color: white; padding: 20px; text-align: center; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🧦 Björn Borg Price Analysis Report</h1>
                    <p>{report_data['report_period']} • Generated {report_data['report_date']}</p>
                </div>
        """
        
        # Add summary section
        if 'summary' in report_data:
            summary = report_data['summary']
            sentiment_colors = {
                "bullish": "#e74c3c", "bearish": "#27ae60", "mixed": "#f39c12", "unknown": "#95a5a6"
            }
            sentiment_color = sentiment_colors.get(summary.get('market_sentiment', 'unknown'), '#95a5a6')
            
            html += f"""
                <div class="summary">
                    <h2>📊 Executive Summary</h2>
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-number">{summary['total_products_tracked']}</div>
                            <div class="stat-label">Products Tracked</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number" style="color: #27ae60;">€{summary['total_savings_potential']:.2f}</div>
                            <div class="stat-label">Total Savings Potential</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number" style="color: {sentiment_color};">{summary['market_sentiment'].title()}</div>
                            <div class="stat-label">Market Sentiment</div>
                        </div>
                    </div>
            """
            
            # Add trend breakdown
            trends = summary['price_trends']
            html += f"""
                    <p><strong>Price Trends:</strong> 
                    📈 {trends['increasing']} increasing • 
                    📉 {trends['decreasing']} decreasing • 
                    ➡️ {trends['stable']} stable</p>
                </div>
            """
        
        # Add individual product analyses
        for product_key, analysis in report_data.get('products', {}).items():
            stats = analysis['price_statistics']
            trends = analysis['trends']
            
            # Trend styling
            trend_class = f"trend-{trends['trend'].replace('increasing', 'up').replace('decreasing', 'down')}"
            trend_icon = {"increasing": "📈", "decreasing": "📉", "stable": "➡️"}.get(trends['trend'], "❓")
            
            # Savings calculation
            savings = stats['current_price'] - stats['lowest_price']
            savings_pct = (savings / stats['current_price']) * 100 if stats['current_price'] > 0 else 0
            
            html += f"""
                <div class="product">
                    <h3>{analysis['product_name']}</h3>
                    <div class="price-info">
                        <div class="price-item">
                            <div class="price-value" style="color: #2c3e50;">€{stats['current_price']:.2f}</div>
                            <div class="price-label">Current Price</div>
                        </div>
                        <div class="price-item">
                            <div class="price-value" style="color: #27ae60;">€{stats['lowest_price']:.2f}</div>
                            <div class="price-label">Best Deal</div>
                        </div>
                        <div class="price-item">
                            <div class="price-value" style="color: #e74c3c;">€{stats['highest_price']:.2f}</div>
                            <div class="price-label">Highest Price</div>
                        </div>
                        <div class="price-item">
                            <div class="price-value" style="color: #3498db;">€{stats['average_price']:.2f}</div>
                            <div class="price-label">Average Price</div>
                        </div>
                    </div>
                    
                    <div style="margin: 15px 0;">
                        <span class="trend {trend_class}">{trend_icon} {trends['trend'].title()}</span>
                        {f'<span style="margin-left: 15px; color: #27ae60; font-weight: bold;">💰 Save €{savings:.2f} ({savings_pct:.1f}%) vs current</span>' if savings > 0.01 else ''}
                    </div>
            """
            
            # Best deals info
            if analysis['best_deals']:
                deal = analysis['best_deals'][0]
                html += f"""<p><strong>🎯 Last Best Deal:</strong> €{deal['price']:.2f} ({deal['days_ago']} days ago)</p>"""
            
            # Seasonal insights
            seasonal = analysis['seasonal_patterns']
            if seasonal.get('analysis') == 'available':
                best_month = seasonal['best_month']
                html += f"""<p><strong>📅 Best Month:</strong> {best_month['month']} (avg: €{best_month['average_price']:.2f})</p>"""
            
            html += f"""<a href="{analysis['purchase_url']}" class="buy-btn">🛒 Buy Now</a></div>"""
        
        html += """
                <div class="footer">
                    <p>🤖 Automated analysis by your Björn Borg price monitoring system</p>
                    <p>📈 Use these insights to time your purchases for maximum savings!</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def send_analysis_report(self, report_data: Dict) -> bool:
        """Send the analysis report via email using EmailSender"""
        
        if "error" in report_data:
            # Send error notification
            subject = "❌ Price Analysis Report - Error"
            html_content = f"""
            <html><body style="font-family: Arial, sans-serif; margin: 20px;">
                <h2 style="color: #e74c3c;">Price Analysis Report Error</h2>
                <p>Unable to generate price analysis report: {report_data['error']}</p>
                <p>This usually means the price monitoring system needs more historical data.</p>
                <p>The analysis will become available after a few days of price tracking.</p>
            </body></html>
            """
        else:
            # Send comprehensive report
            period = report_data['report_period']
            total_products = report_data.get('summary', {}).get('total_products_tracked', 0)
            
            subject = f"📊 {period} - {total_products} Products Analyzed"
            html_content = self.format_html_report(report_data)
        
        # Use EmailSender's method instead of duplicating logic
        try:
            success = self.email_sender.send_analysis_report(subject, html_content)
            if success:
                print(f"✅ Analysis report sent successfully")
            else:
                print(f"❌ Failed to send analysis report")
            return success
                
        except Exception as e:
            print(f"❌ Failed to send analysis report: {e}")
            return False
    
    def save_report_files(self, report_data: Dict) -> None:
        """Save report as text and HTML files"""
        
        timestamp = self.report_date.strftime("%Y-%m-%d_%H-%M-%S")
        
        # Save as JSON
        with open(f"price_analysis_{timestamp}.json", 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        # Save as HTML
        if "error" not in report_data:
            html_content = self.format_html_report(report_data)
            with open(f"price_analysis_{timestamp}.html", 'w', encoding='utf-8') as f:
                f.write(html_content)
        
        print(f"📄 Report files saved with timestamp: {timestamp}")

def main():
    """Generate and send automated price analysis report"""
    
    print("📊 Starting automated price analysis report generation...")
    
    reporter = PriceAnalysisReporter()
    
    # Generate comprehensive report
    report_data = reporter.generate_comprehensive_report()
    
    # Save report files (for GitHub Actions artifacts)
    reporter.save_report_files(report_data)
    
    # Send via email
    success = reporter.send_analysis_report(report_data)
    
    if success:
        print("🎉 Price analysis report generated and sent successfully!")
    else:
        print("❌ Failed to send price analysis report")
        exit(1)

if __name__ == "__main__":
    main()