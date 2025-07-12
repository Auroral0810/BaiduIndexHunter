import pandas as pd
import numpy as np
from datetime import datetime
import os
from itertools import product


class MonthlyDataAggregator:
    def __init__(self, input_file_path, output_dir="./output"):
        """
        初始化月度数据统计器

        Args:
            input_file_path: 输入文件路径
            output_dir: 输出目录
        """
        self.input_file_path = input_file_path
        self.output_dir = output_dir

        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)

        # 列名映射
        self.column_mapping = {
            '关键词': 'keyword',
            '城市代码': 'city_code',
            '城市': 'city_name',
            '日期': 'date',
            '数据类型': 'data_type',
            '数据间隔(天)': 'data_interval',
            '所属年份': 'year',
            'PC+移动指数': 'pc_mobile_index',
            '移动指数': 'mobile_index',
            'PC指数': 'pc_index',
            '爬取时间': 'crawl_time'
        }

    def load_data(self):
        """加载数据文件"""
        try:
            # 根据文件扩展名选择读取方式
            if self.input_file_path.endswith('.csv'):
                df = pd.read_csv(self.input_file_path, encoding='utf-8')
            elif self.input_file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(self.input_file_path)
            else:
                # 尝试以制表符分隔的文本文件读取
                df = pd.read_csv(self.input_file_path, sep='\t', encoding='utf-8')

            print(f"成功加载数据，共 {len(df)} 行")
            return df

        except Exception as e:
            print(f"加载数据失败: {e}")
            return None

    def preprocess_data(self, df):
        """预处理数据"""
        try:
            # 重命名列（如果需要）
            if '关键词' in df.columns:
                df = df.rename(columns=self.column_mapping)

            # 转换日期格式
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'], errors='coerce')
            else:
                print("未找到日期列")
                return None

            # 创建年月列
            df['year_month'] = df['date'].dt.strftime('%Y-%m')
            df['year'] = df['date'].dt.year
            df['month'] = df['date'].dt.month

            # 转换数值列，处理空值
            numeric_columns = ['pc_mobile_index', 'mobile_index', 'pc_index']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            # 删除无效日期的行
            # df = df.dropna(subset=['date'])

            # 删除所有指数都为空的行
            # df = df.dropna(subset=numeric_columns, how='all')

            print(f"数据预处理完成，有效数据 {len(df)} 行")
            print(f"日期范围: {df['date'].min()} 到 {df['date'].max()}")

            return df

        except Exception as e:
            print(f"数据预处理失败: {e}")
            return None

    def create_complete_monthly_template(self, df):
        """创建完整的月度模板，为每个关键词-城市组合创建其各自的完整时间范围"""
        try:
            # 获取每个关键词-城市组合的时间范围
            combo_date_ranges = df.groupby(['keyword', 'city_code', 'city_name'])['date'].agg(['min', 'max']).reset_index()
            
            print(f"创建完整月度模板:")
            print(f"  关键词-城市组合数: {len(combo_date_ranges)}")
            
            # 创建完整的组合
            complete_combinations = []
            total_months = 0
            
            for _, combo in combo_date_ranges.iterrows():
                # 为每个组合创建从其最小日期到最大日期的所有月份
                min_date = combo['min'].replace(day=1)  # 月初
                max_date = combo['max'].replace(day=1)  # 月初
                
                # 创建该组合的月份范围
                date_range = pd.date_range(start=min_date, end=max_date, freq='MS')
                year_months = [date.strftime('%Y-%m') for date in date_range]
                
                # 为该组合添加所有月份
                for year_month in year_months:
                    complete_combinations.append({
                        'keyword': combo['keyword'],
                        'city_code': combo['city_code'],
                        'city_name': combo['city_name'],
                        'year_month': year_month,
                        'year': int(year_month.split('-')[0]),
                        'month': int(year_month.split('-')[1])
                    })
                
                total_months += len(year_months)
            
            template_df = pd.DataFrame(complete_combinations)
            
            print(f"  理论记录数: {total_months}")
            print(f"  实际创建模板记录数: {len(template_df)}")
            
            # 显示一些统计信息
            if len(template_df) > 0:
                earliest_month = template_df['year_month'].min()
                latest_month = template_df['year_month'].max()
                print(f"  整体时间范围: {earliest_month} 到 {latest_month}")
                
                # 显示每个关键词的统计
                keyword_stats = template_df.groupby('keyword')['year_month'].agg(['min', 'max', 'count']).reset_index()
                keyword_stats.columns = ['keyword', 'start_month', 'end_month', 'month_count']
                print(f"  各关键词时间跨度:")
                for _, row in keyword_stats.iterrows():
                    print(f"    {row['keyword']}: {row['start_month']} 到 {row['end_month']} ({row['month_count']} 个月)")
            
            return template_df
            
        except Exception as e:
            print(f"创建月度模板失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    def aggregate_monthly_data(self, df):
        """按月度聚合数据"""
        try:
            # 分组列
            group_columns = ['keyword', 'city_code', 'city_name', 'year_month', 'year', 'month']

            # 数值列
            numeric_columns = ['pc_mobile_index', 'mobile_index', 'pc_index']

            # 聚合统计
            agg_dict = {}

            # 为每个数值列创建统计量
            for col in numeric_columns:
                if col in df.columns:
                    agg_dict[col] = ['sum', 'mean', 'count', 'min', 'max', 'std']

            # 执行聚合
            monthly_data = df.groupby(group_columns).agg(agg_dict).reset_index()

            # 处理多级列名
            new_columns = []
            for col in monthly_data.columns:
                if isinstance(col, tuple) and len(col) == 2:
                    base_col, agg_type = col
                    if agg_type == 'sum':
                        new_columns.append(f'{base_col}_月度总和')
                    elif agg_type == 'mean':
                        new_columns.append(f'{base_col}_月度均值')
                    elif agg_type == 'count':
                        new_columns.append(f'{base_col}_数据点数')
                    elif agg_type == 'min':
                        new_columns.append(f'{base_col}_月度最小值')
                    elif agg_type == 'max':
                        new_columns.append(f'{base_col}_月度最大值')
                    elif agg_type == 'std':
                        new_columns.append(f'{base_col}_月度标准差')
                    else:
                        new_columns.append(f'{base_col}_{agg_type}')
                else:
                    new_columns.append(col)

            monthly_data.columns = new_columns

            # 对数值列进行四舍五入
            for col in monthly_data.columns:
                if any(suffix in col for suffix in ['_均值', '_标准差']):
                    monthly_data[col] = monthly_data[col].round(2)

            print(f"月度数据聚合完成，共 {len(monthly_data)} 行")
            
            return monthly_data

        except Exception as e:
            print(f"月度数据聚合失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    def create_complete_monthly_data(self, df):
        """创建完整的月度数据，包含缺失月份的记录"""
        try:
            # 先进行正常的月度聚合
            monthly_data = self.aggregate_monthly_data(df)
            if monthly_data is None:
                return None
            
            # 创建完整的月度模板
            template_df = self.create_complete_monthly_template(df)
            if template_df is None:
                return None
            
            print(f"准备合并数据:")
            print(f"  模板数据形状: {template_df.shape}")
            print(f"  聚合数据形状: {monthly_data.shape}")
            
            # 检查列名
            print(f"  模板列名: {template_df.columns.tolist()}")
            print(f"  聚合数据列名: {monthly_data.columns.tolist()}")
            
            # 确保列名匹配 - 检查monthly_data中的列名是否与模板匹配
            # 如果monthly_data中的列名不是预期的格式，需要重命名
            if 'keyword_' in monthly_data.columns:
                # 列名可能有后缀，需要重命名
                column_mapping = {
                    'keyword_': 'keyword',
                    'city_code_': 'city_code',
                    'city_name_': 'city_name',
                    'year_month_': 'year_month',
                    'year_': 'year',
                    'month_': 'month'
                }
                monthly_data = monthly_data.rename(columns=column_mapping)
                print(f"  已重命名列，现在聚合数据列名: {monthly_data.columns.tolist()}")
            
            # 将聚合数据与模板合并，确保所有组合都存在
            complete_monthly_data = template_df.merge(
                monthly_data, 
                on=['keyword', 'city_code', 'city_name', 'year_month', 'year', 'month'],
                how='left'
            )
            
            print(f"合并后数据形状: {complete_monthly_data.shape}")
            
            # 为缺失的数据添加标识
            complete_monthly_data['has_data'] = complete_monthly_data['pc_mobile_index_数据点数'].notna()
            
            # 统计缺失情况
            total_records = len(complete_monthly_data)
            records_with_data = complete_monthly_data['has_data'].sum()
            records_without_data = total_records - records_with_data
            
            print(f"完整月度数据创建完成:")
            print(f"  总记录数: {total_records}")
            print(f"  有数据记录数: {records_with_data}")
            print(f"  无数据记录数: {records_without_data}")
            print(f"  数据覆盖率: {records_with_data/total_records*100:.1f}%")
            
            return complete_monthly_data

        except Exception as e:
            print(f"创建完整月度数据失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    def analyze_data_coverage(self, df):
        """分析数据覆盖情况"""
        try:
            print("\n数据覆盖分析:")
            print("=" * 50)
            
            # 按关键词-城市组合分析时间跨度
            combo_analysis = df.groupby(['keyword', 'city_code', 'city_name']).agg({
                'date': ['min', 'max', 'count'],
                'year_month': 'nunique'
            }).reset_index()
            
            # 展平多级列名
            combo_analysis.columns = ['keyword', 'city_code', 'city_name', 'first_date', 'last_date', 'total_days', 'unique_months']
            
            # 计算时间跨度（月份）
            combo_analysis['months_span'] = (
                (combo_analysis['last_date'].dt.year - combo_analysis['first_date'].dt.year) * 12 + 
                (combo_analysis['last_date'].dt.month - combo_analysis['first_date'].dt.month) + 1
            )
            
            # 计算覆盖率
            combo_analysis['coverage_rate'] = (combo_analysis['unique_months'] / combo_analysis['months_span'] * 100).round(1)
            
            print(f"关键词-城市组合总数: {len(combo_analysis)}")
            print(f"平均时间跨度: {combo_analysis['months_span'].mean():.1f} 个月")
            print(f"平均覆盖率: {combo_analysis['coverage_rate'].mean():.1f}%")
            
            # 显示覆盖率分布
            print("\n覆盖率分布:")
            coverage_ranges = [
                (0, 50, "低覆盖 (0-50%)"),
                (50, 80, "中等覆盖 (50-80%)"),
                (80, 95, "高覆盖 (80-95%)"),
                (95, 100, "极高覆盖 (95-100%)")
            ]
            
            for min_rate, max_rate, label in coverage_ranges:
                count = len(combo_analysis[
                    (combo_analysis['coverage_rate'] >= min_rate) & 
                    (combo_analysis['coverage_rate'] <= max_rate)
                ])
                percentage = count / len(combo_analysis) * 100
                print(f"  {label}: {count} 个组合 ({percentage:.1f}%)")
            
            # 显示时间跨度最长和最短的组合
            print(f"\n时间跨度最长的组合:")
            longest = combo_analysis.nlargest(3, 'months_span')
            for _, row in longest.iterrows():
                print(f"  {row['keyword']} - {row['city_name']}: {row['months_span']} 个月 "
                      f"({row['first_date'].strftime('%Y-%m')} 到 {row['last_date'].strftime('%Y-%m')})")
            
            print(f"\n时间跨度最短的组合:")
            shortest = combo_analysis.nsmallest(3, 'months_span')
            for _, row in shortest.iterrows():
                print(f"  {row['keyword']} - {row['city_name']}: {row['months_span']} 个月 "
                      f"({row['first_date'].strftime('%Y-%m')} 到 {row['last_date'].strftime('%Y-%m')})")
            
            return combo_analysis
            
        except Exception as e:
            print(f"数据覆盖分析失败: {e}")
            return None

    def generate_summary_report(self, df, monthly_data):
        """生成统计报告"""
        try:
            report = []
            report.append("=" * 80)
            report.append("月度数据统计报告")
            report.append("=" * 80)

            # 基础统计信息
            report.append(f"原始数据总行数: {len(df):,}")
            report.append(f"月度数据总行数: {len(monthly_data):,}")
            report.append(f"关键词数量: {df['keyword'].nunique()}")
            report.append(f"城市数量: {df['city_name'].nunique()}")
            report.append(f"关键词-城市组合数: {len(df[['keyword', 'city_name']].drop_duplicates())}")

            # 时间范围
            date_range = f"{df['date'].min().strftime('%Y-%m-%d')} 到 {df['date'].max().strftime('%Y-%m-%d')}"
            report.append(f"数据时间范围: {date_range}")

            # 数据完整性统计
            if 'has_data' in monthly_data.columns:
                total_records = len(monthly_data)
                records_with_data = monthly_data['has_data'].sum()
                coverage_rate = records_with_data / total_records * 100
                report.append(f"月度数据覆盖率: {coverage_rate:.1f}% ({records_with_data:,}/{total_records:,})")

            # 按关键词统计
            report.append("\n" + "=" * 50)
            report.append("按关键词统计:")
            report.append("=" * 50)
            
            for keyword in df['keyword'].unique():
                keyword_data = df[df['keyword'] == keyword]
                keyword_monthly = monthly_data[monthly_data['keyword'] == keyword]
                
                report.append(f"\n关键词: {keyword}")
                report.append(f"  原始数据点数: {len(keyword_data):,}")
                report.append(f"  月度记录数: {len(keyword_monthly):,}")
                report.append(f"  城市数量: {keyword_data['city_name'].nunique()}")
                report.append(f"  时间范围: {keyword_data['date'].min().strftime('%Y-%m-%d')} 到 {keyword_data['date'].max().strftime('%Y-%m-%d')}")
                
                if 'has_data' in keyword_monthly.columns:
                    keyword_coverage = keyword_monthly['has_data'].sum() / len(keyword_monthly) * 100
                    report.append(f"  数据覆盖率: {keyword_coverage:.1f}%")
                
                if 'pc_mobile_index_月度均值' in keyword_monthly.columns:
                    avg_index = keyword_monthly['pc_mobile_index_月度均值'].mean()
                    if not pd.isna(avg_index):
                        report.append(f"  平均月度PC+移动指数: {avg_index:.2f}")

            # 按年份统计
            report.append("\n" + "=" * 50)
            report.append("按年份统计:")
            report.append("=" * 50)
            
            for year in sorted(monthly_data['year'].unique()):
                year_data = monthly_data[monthly_data['year'] == year]
                if 'has_data' in year_data.columns:
                    year_coverage = year_data['has_data'].sum() / len(year_data) * 100
                    report.append(f"{year}年: 覆盖率 {year_coverage:.1f}% ({year_data['has_data'].sum():,}/{len(year_data):,})")

            # 缺失数据分析
            if 'has_data' in monthly_data.columns:
                missing_data = monthly_data[monthly_data['has_data'] == False]
                if len(missing_data) > 0:
                    report.append(f"\n缺失数据分析:")
                    report.append(f"缺失记录总数: {len(missing_data):,}")
                    
                    # 按关键词-城市组合统计缺失情况
                    missing_by_combo = missing_data.groupby(['keyword', 'city_name']).size().sort_values(ascending=False)
                    report.append(f"缺失最多的关键词-城市组合 (前10):")
                    for (keyword, city), count in missing_by_combo.head(10).items():
                        report.append(f"  {keyword} - {city}: {count} 个月")

            report.append("\n" + "=" * 80)

            return "\n".join(report)

        except Exception as e:
            print(f"生成统计报告失败: {e}")
            return "统计报告生成失败"

    def save_results(self, monthly_data, report):
        """保存结果"""
        try:
            # 保存月度数据
            monthly_file = os.path.join(self.output_dir, "monthly_aggregated_data.xlsx")
            
            # 创建Excel文件，包含多个工作表
            with pd.ExcelWriter(monthly_file, engine='openpyxl') as writer:
                # 保存完整数据
                monthly_data.to_excel(writer, sheet_name='完整月度数据', index=False)
                
                # 保存只有数据的记录
                if 'has_data' in monthly_data.columns:
                    data_only = monthly_data[monthly_data['has_data'] == True]
                    data_only.to_excel(writer, sheet_name='有数据月度记录', index=False)
                    
                    # 保存缺失数据记录
                    missing_only = monthly_data[monthly_data['has_data'] == False]
                    missing_only.to_excel(writer, sheet_name='缺失数据记录', index=False)
                
                # 保存统计摘要
                summary_stats = self.create_summary_statistics(monthly_data)
                summary_stats.to_excel(writer, sheet_name='统计摘要', index=False)
            
            print(f"月度数据已保存到: {monthly_file}")

            # 同时保存CSV格式（完整数据）
            csv_file = os.path.join(self.output_dir, "monthly_aggregated_data.csv")
            monthly_data.to_csv(csv_file, index=False, encoding='utf-8-sig')
            print(f"月度数据已保存到: {csv_file}")

            # 保存为 DTA 文件
            try:
                monthly_file_dta = os.path.join(self.output_dir, "monthly_aggregated_data.dta")
                # 处理列名长度限制
                monthly_data_for_stata = monthly_data.copy()
                monthly_data_for_stata.columns = [col[:32] for col in monthly_data_for_stata.columns]
                monthly_data_for_stata.to_stata(monthly_file_dta, version=118)
                print(f"月度数据已保存到: {monthly_file_dta}")
            except Exception as e:
                print(f"保存DTA文件失败: {e}")

            # 保存统计报告
            report_file = os.path.join(self.output_dir, "monthly_report.txt")
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"统计报告已保存到: {report_file}")

            return True

        except Exception as e:
            print(f"保存结果失败: {e}")
            return False

    def create_summary_statistics(self, monthly_data):
        """创建统计摘要"""
        try:
            summary_list = []
            
            # 按关键词统计
            if 'has_data' in monthly_data.columns:
                keyword_stats = monthly_data.groupby('keyword').agg({
                    'city_name': 'nunique',
                    'year_month': 'nunique',
                    'has_data': ['sum', 'count']
                }).round(2)
                
                keyword_stats.columns = ['城市数', '月份数', '有数据月份数', '总月份数']
                keyword_stats['数据覆盖率'] = (keyword_stats['有数据月份数'] / keyword_stats['总月份数'] * 100).round(1)
                keyword_stats = keyword_stats.reset_index()
                
                return keyword_stats
            else:
                return pd.DataFrame()
            
        except Exception as e:
            print(f"创建统计摘要失败: {e}")
            return pd.DataFrame()

    def process(self):
        """主处理流程"""
        print("开始处理月度数据统计...")

        # 1. 加载数据
        df = self.load_data()
        if df is None:
            return False

        # 2. 预处理数据
        df = self.preprocess_data(df)
        if df is None:
            return False

        # 3. 分析数据覆盖情况
        coverage_analysis = self.analyze_data_coverage(df)

        # 4. 创建完整的月度数据
        monthly_data = self.create_complete_monthly_data(df)
        if monthly_data is None:
            return False

        # 5. 生成统计报告
        report = self.generate_summary_report(df, monthly_data)

        # 6. 保存结果
        success = self.save_results(monthly_data, report)

        if success:
            print("\n处理完成！")
            print(report)

        return success


# 使用示例
def main():
    # 配置文件路径
    input_file = "/Users/auroral/ProjectDevelopment/BaiduIndexHunter/unique_sample_data.csv"
    output_directory = "/Users/auroral/ProjectDevelopment/BaiduIndexHunter/baidu-index-hunter-backend/data_progress"

    # 创建处理器实例
    aggregator = MonthlyDataAggregator(input_file, output_directory)

    # 执行处理
    success = aggregator.process()

    if success:
        print("\n✅ 月度数据统计完成！")
        print(f"📁 结果文件保存在: {output_directory}")
        print("📊 生成的文件:")
        print("   - monthly_aggregated_data.xlsx (Excel格式，包含多个工作表)")
        print("   - monthly_aggregated_data.csv (CSV格式)")
        print("   - monthly_aggregated_data.dta (Stata格式)")
        print("   - monthly_report.txt (统计报告)")
    else:
        print("\n❌ 处理失败！")


if __name__ == "__main__":
    main()


# 简化版本的函数，考虑每个组合的实际时间跨度
def simple_monthly_aggregation_with_individual_ranges(df):
    """
    改进的简化月度聚合函数，为每个关键词-城市组合创建其各自的完整时间范围

    Args:
        df: 包含日期和指数数据的DataFrame

    Returns:
        complete_monthly_data: 完整的月度数据，包含缺失月份
    """
    # 确保日期列是datetime类型
    df['date'] = pd.to_datetime(df['date'])
    df['year_month'] = df['date'].dt.strftime('%Y-%m')
    
    # 获取每个关键词-城市组合的时间范围
    combo_ranges = df.groupby(['keyword', 'city_code', 'city_name'])['date'].agg(['min', 'max']).reset_index()
    
    # 为每个组合创建完整的月份模板
    template_data = []
    for _, combo in combo_ranges.iterrows():
        # 创建从最小日期到最大日期的所有月份
        min_date = combo['min'].replace(day=1)
        max_date = combo['max'].replace(day=1)
        
        date_range = pd.date_range(start=min_date, end=max_date, freq='MS')
        year_months = [date.strftime('%Y-%m') for date in date_range]
        
        for ym in year_months:
            template_data.append({
                'keyword': combo['keyword'],
                'city_code': combo['city_code'],
                'city_name': combo['city_name'],
                'year_month': ym
            })
    
    template_df = pd.DataFrame(template_data)
    
    # 聚合实际数据
    monthly_aggregated = df.groupby(['keyword', 'city_code', 'city_name', 'year_month']).agg({
        'pc_mobile_index': ['sum', 'mean', 'count'],
        'mobile_index': ['sum', 'mean', 'count'],
        'pc_index': ['sum', 'mean', 'count']
    }).reset_index()
    
    # 处理列名
    new_columns = ['keyword', 'city_code', 'city_name', 'year_month']
    for col in ['pc_mobile_index', 'mobile_index', 'pc_index']:
        new_columns.extend([f'{col}_月度总和', f'{col}_月度均值', f'{col}_数据点数'])
    
    monthly_aggregated.columns = new_columns
    
    # 与模板合并
    complete_monthly_data = template_df.merge(monthly_aggregated, 
                                            on=['keyword', 'city_code', 'city_name', 'year_month'],
                                            how='left')
    
    # 添加数据标识
    complete_monthly_data['has_data'] = complete_monthly_data['pc_mobile_index_数据点数'].notna()
    
    print(f"完整月度数据创建完成:")
    print(f"  总记录数: {len(complete_monthly_data)}")
    print(f"  有数据记录数: {complete_monthly_data['has_data'].sum()}")
    print(f"  数据覆盖率: {complete_monthly_data['has_data'].sum()/len(complete_monthly_data)*100:.1f}%")
    
    return complete_monthly_data