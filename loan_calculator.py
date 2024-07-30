from pathlib import Path

import pandas as pd
from tabulate import tabulate


# 读取配置文件
def read_config(config_file):
    config = {}
    with open(config_file, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            if line and not line.startswith('#'):
                key, value = line.split('=')
                config[key.strip()] = float(value.strip())
    return config


# 计算等额本息月供
def calculate_equal_interest_monthly_payment(principal, annual_rate, periods):
    """
    计算等额本息月供
    :param principal: 贷款本金
    :param annual_rate: 年利率
    :param periods: 还款总月数
    :return: 每月还款额
    """
    monthly_rate = annual_rate / 100 / 12  # 转换为月利率
    return principal * monthly_rate * (1 + monthly_rate) ** periods / ((1 + monthly_rate) ** periods - 1)


# 计算等额本金涉及的月供（首月、末月和每月递减金额）及总利息
def calculate_equal_principal_monthly_payment(principal, annual_rate, periods):
    """
    计算等额本金的首月、末月还款金额，每月递减金额及总利息
    :param principal: 贷款本金
    :param annual_rate: 年利率
    :param periods: 还款总月数
    :return: 首月还款额, 末月还款额, 每月递减金额, 总支付利息
    """
    monthly_rate = annual_rate / 100 / 12  # 转换为月利率
    monthly_principal = principal / periods  # 每月应还的本金
    interest_first_month = principal * monthly_rate  # 首月利息
    total_interest = 0

    # 计算每月的利息总和
    for month in range(int(periods)):
        monthly_interest = (principal - month * monthly_principal) * monthly_rate  # 当月利息
        total_interest += monthly_interest

    # 首月还款 = 每月本金 + 首月利息
    first_month_payment = monthly_principal + interest_first_month
    # 末月还款 = 每月本金 + 末月利息
    last_month_payment = monthly_principal + (monthly_principal * monthly_rate)
    # 每月递减金额 = 每月本金 * 月利率
    monthly_decrease = monthly_principal * monthly_rate

    return first_month_payment, last_month_payment, monthly_decrease, total_interest / 10000


# 计算所有结果
def calculate_results(config, repayment_method):
    house_price = config['house_price']
    down_payment_ratio = config['down_payment_ratio'] / 100
    fund_loan_amount = config['fund_loan_amount']
    fund_loan_rate = config['fund_loan_rate']
    deed_tax_rate = config['deed_tax_rate'] / 100
    loan_years = config['loan_years']
    agent_fee_ratio = config['agent_fee_ratio'] / 100
    commercial_loan_rate = config['commercial_loan_rate']

    # 计算基础值
    down_payment = house_price * down_payment_ratio  # 首付款
    total_loan_amount = house_price - down_payment  # 总贷款金额
    commercial_loan_amount = total_loan_amount - fund_loan_amount  # 商业贷款金额

    periods = loan_years * 12  # 还款总月数
    if repayment_method == 'equal_interest':
        # 计算等额本息下的月供和总利息
        fund_monthly_payment = calculate_equal_interest_monthly_payment(fund_loan_amount * 10000, fund_loan_rate,
                                                                        periods)
        commercial_monthly_payment = calculate_equal_interest_monthly_payment(commercial_loan_amount * 10000,
                                                                              commercial_loan_rate, periods)

        # 月供
        monthly_payment_fund = fund_monthly_payment
        monthly_payment_commercial = commercial_monthly_payment
        total_monthly_payment = monthly_payment_fund + monthly_payment_commercial

        # 总支付利息
        total_interest_fund = (monthly_payment_fund * periods - fund_loan_amount * 10000) / 10000  # 公积金贷款总利息
        total_interest_commercial = (
                                            monthly_payment_commercial * periods - commercial_loan_amount * 10000) / 10000  # 商业贷款总利息
        total_interest = total_interest_fund + total_interest_commercial  # 总利息

        result = {
            '月供(元)': f"{total_monthly_payment:.2f}",
            '总支付利息(万元)': f"{total_interest:.2f}",
        }

    elif repayment_method == 'equal_principal':
        # 计算等额本金下的首月、末月还款金额，每月递减金额和总利息
        fund_first_month, fund_last_month, fund_monthly_decrease, total_interest_fund = calculate_equal_principal_monthly_payment(
            fund_loan_amount * 10000, fund_loan_rate, periods)
        commercial_first_month, commercial_last_month, commercial_monthly_decrease, total_interest_commercial = calculate_equal_principal_monthly_payment(
            commercial_loan_amount * 10000, commercial_loan_rate, periods)

        # 首月还款 = 公积金贷款首月 + 商业贷款首月
        first_month_payment = fund_first_month + commercial_first_month
        # 末月还款 = 公积金贷款末月 + 商业贷款末月
        last_month_payment = fund_last_month + commercial_last_month
        # 每月递减金额 = 公积金贷款每月递减 + 商业贷款每月递减
        monthly_decrease = fund_monthly_decrease + commercial_monthly_decrease

        total_interest = total_interest_fund + total_interest_commercial  # 总利息

        result = {
            '首月还款额(元)': f"{first_month_payment:.2f}",
            '末月还款额(元)': f"{last_month_payment:.2f}",
            '每月递减金额(元)': f"{monthly_decrease:.2f}",
            '总支付利息(万元)': f"{total_interest:.2f}",
        }

    total_interest_payment = result['总支付利息(万元)']  # 总支付利息
    total_payment = total_loan_amount + float(total_interest_payment)  # 本金+利息
    deed_tax = house_price * deed_tax_rate  # 契税
    agent_fee = house_price * agent_fee_ratio  # 中介费
    # 装修费用合计
    decoration_cost = sum([
        config['hard_deco'],
        config['whole_house_custom'],
        config['doors_and_windows'],
        config['soft_furnishings'],
        config['appliance'],
        config['miscellaneous']
    ]) / 10000
    total_budget_without_decoration = down_payment + deed_tax + agent_fee  # 总预算不带装修
    total_budget_with_decoration = total_budget_without_decoration + decoration_cost  # 总预算带装修
    total_expense_with_interest_without_decoration = total_budget_without_decoration + total_payment  # 带利息总花费（不带装修）
    total_expense_with_interest_with_decoration = total_budget_with_decoration + total_payment  # 带利息总花费（带装修）

    # 组装详细结果字典
    details = {
        '房屋总价(万元)': f"{house_price:.2f}",
        '首付比例': f"{down_payment_ratio * 100:.2f}%",
        '首付款(万元)': f"{down_payment:.2f}",
        '贷款金额(万元)': f"{total_loan_amount:.2f}",
        '公积金贷款金额(万元)': f"{fund_loan_amount:.2f}",
        '商业贷款金额(万元)': f"{commercial_loan_amount:.2f}",
        '公积金贷款比例': f"{fund_loan_amount / total_loan_amount:.2%}",
        '商业贷款比例': f"{commercial_loan_amount / total_loan_amount:.2%}",
        '公积金贷款利率': f"{fund_loan_rate:.2f}%",
        '商业贷款利率': f"{commercial_loan_rate:.2f}%",
        '贷款期限(年)': f"{loan_years:.0f}",
        '契税(万元)': f"{deed_tax:.2f}",
        '中介费(万元)': f"{agent_fee:.2f}",
        '装修费(万元)': f"{decoration_cost:.2f}",
        '贷款总支付金额(万元)': f"{total_payment:.2f}",
        '总预算不带装修(万元)': f"{total_budget_without_decoration:.2f}",
        '总预算带装修(万元)': f"{total_budget_with_decoration:.2f}",
        '总花费带利息不带装修（万元）': f"{total_expense_with_interest_without_decoration:.2f}",
        '总花费带利息带装修（万元）': f"{total_expense_with_interest_with_decoration:.2f}"
    }

    details.update(result)

    return details


# 输出结果
def output_results(config, method):
    results = calculate_results(config, method)
    return results


# 程序入口
def main():
    # 定义项目路径和文件
    project_path = Path(__file__).resolve().parent

    config_file = project_path / 'config.txt'

    # 读取配置文件
    config = read_config(config_file)

    # 创建4个视图
    views_names = [
        '组合贷款方案-等额本息',
        '组合贷款方案-等额本金',
        '纯商业贷款方案-等额本息',
        '纯商业贷款方案-等额本金'
    ]

    views = {}
    # 计算组合贷款方案-等额本息
    views['组合贷款方案-等额本息'] = output_results(config, 'equal_interest')
    # 计算组合贷款方案-等额本金
    views['组合贷款方案-等额本金'] = output_results(config, 'equal_principal')

    # 设置无公积金贷款情景，并计算纯商业贷款方案
    config['fund_loan_amount'] = 0
    views['纯商业贷款方案-等额本息'] = output_results(config, 'equal_interest')
    views['纯商业贷款方案-等额本金'] = output_results(config, 'equal_principal')

    # 输出到Excel文件
    with pd.ExcelWriter(project_path / 'loan_results.xlsx') as writer:
        for view_name, results in views.items():
            df = pd.DataFrame([results])
            df.to_excel(writer, sheet_name=view_name, index=False)

    # 保存到Markdown文件
    save_markdown(views, project_path / 'loan_results.md')

    # 在命令行中打印结果
    for view_name, results in views.items():
        print(f'\n{view_name}')
        print(tabulate(results.items(), headers=['项目', '数值'], tablefmt='pretty'))


def save_markdown(views, output_path):
    """保存计算结果到Markdown文件"""
    with open(output_path, 'w', encoding='utf-8') as f:
        for view_name, results in views.items():
            f.write(f'## {view_name}\n')
            table = tabulate(results.items(), headers=['项目', '数值'], tablefmt='pipe', stralign='center',
                             numalign='center')
            f.write(f"{table}\n\n")


if __name__ == '__main__':
    main()
