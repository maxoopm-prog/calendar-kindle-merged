"""
万年历 - 完全基于 https://github.com/mircode/calender 项目转译
基准点：1899年2月10日（农历1899年1月1日）
"""

class Calendar:
    """万年历核心算法"""
    
    # 农历数据 (1899-2100)  
    LUNAR_INFO = [
        0x0ab50,  # 1899
        0x04bd8, 0x04ae0, 0x0a570, 0x054d5, 0x0d260, 0x0d950, 0x16554, 0x056a0, 0x09ad0, 0x055d2,  # 1900-1909
        0x04ae0, 0x0a5b6, 0x0a4d0, 0x0d250, 0x1d255, 0x0b540, 0x0d6a0, 0x0ada2, 0x095b0, 0x14977,  # 1910-1919
        0x04970, 0x0a4b0, 0x0b4b5, 0x06a50, 0x06d40, 0x1ab54, 0x02b60, 0x09570, 0x052f2, 0x04970,  # 1920-1929
        0x06566, 0x0d4a0, 0x0ea50, 0x06e95, 0x05ad0, 0x02b60, 0x186e3, 0x092e0, 0x1c8d7, 0x0c950,  # 1930-1939
        0x0d4a0, 0x1d8a6, 0x0b550, 0x056a0, 0x1a5b4, 0x025d0, 0x092d0, 0x0d2b2, 0x0a950, 0x0b557,  # 1940-1949
        0x06ca0, 0x0b550, 0x15355, 0x04da0, 0x0a5b0, 0x14573, 0x052b0, 0x0a9a8, 0x0e950, 0x06aa0,  # 1950-1959
        0x0aea6, 0x0ab50, 0x04b60, 0x0aae4, 0x0a570, 0x05260, 0x0f263, 0x0d950, 0x05b57, 0x056a0,  # 1960-1969
        0x096d0, 0x04dd5, 0x04ad0, 0x0a4d0, 0x0d4d4, 0x0d250, 0x0d558, 0x0b540, 0x0b6a0, 0x195a6,  # 1970-1979
        0x095b0, 0x049b0, 0x0a974, 0x0a4b0, 0x0b27a, 0x06a50, 0x06d40, 0x0af46, 0x0ab60, 0x09570,  # 1980-1989
        0x04af5, 0x04970, 0x064b0, 0x074a3, 0x0ea50, 0x06b58, 0x055c0, 0x0ab60, 0x096d5, 0x092e0,  # 1990-1999
        0x0c960, 0x0d954, 0x0d4a0, 0x0da50, 0x07552, 0x056a0, 0x0abb7, 0x025d0, 0x092d0, 0x0cab5,  # 2000-2009
        0x0a950, 0x0b4a0, 0x0baa4, 0x0ad50, 0x055d9, 0x04ba0, 0x0a5b0, 0x15176, 0x052b0, 0x0a930,  # 2010-2019
        0x07954, 0x06aa0, 0x0ad50, 0x05b52, 0x04b60, 0x0a6e6, 0x0a4e0, 0x0d260, 0x0ea65, 0x0d530,  # 2020-2029
        0x05aa0, 0x076a3, 0x096d0, 0x04bd7, 0x04ad0, 0x0a4d0, 0x1d0b6, 0x0d250, 0x0d520, 0x0dd45,  # 2030-2039
        0x0b5a0, 0x056d0, 0x055b2, 0x049b0, 0x0a577, 0x0a4b0, 0x0aa50, 0x1b255, 0x06d20, 0x0ada0,  # 2040-2049
        0x14b63, 0x09370, 0x049f8, 0x04970, 0x064b0, 0x168a6, 0x0ea50, 0x06b20, 0x1a6c4, 0x0aae0,  # 2050-2059
        0x0a2e0, 0x0d2e3, 0x0c960, 0x0d557, 0x0d4a0, 0x0da50, 0x05d55, 0x056a0, 0x0a6d0, 0x055d4,  # 2060-2069
        0x052d0, 0x0a9b8, 0x0a950, 0x0b4a0, 0x0b6a6, 0x0ad50, 0x055a0, 0x0aba4, 0x0a5b0, 0x052b0,  # 2070-2079
        0x0b273, 0x06930, 0x07337, 0x06aa0, 0x0ad50, 0x14b55, 0x04b60, 0x0a570, 0x054e4, 0x0d160,  # 2080-2089
        0x0e968, 0x0d520, 0x0daa0, 0x16aa6, 0x056d0, 0x04ae0, 0x0a9d4, 0x0a2d0, 0x0d150, 0x0f252,  # 2090-2099
        0x0d520,  # 2100
    ]
    
    LUNAR_MONTH = ['正月', '二月', '三月', '四月', '五月', '六月', 
                   '七月', '八月', '九月', '十月', '十一月', '十二月']
    
    LUNAR_DAY = ['初一', '初二', '初三', '初四', '初五', '初六', '初七', '初八', '初九', '初十',
                 '十一', '十二', '十三', '十四', '十五', '十六', '十七', '十八', '十九', '二十',
                 '廿一', '廿二', '廿三', '廿四', '廿五', '廿六', '廿七', '廿八', '廿九', '三十', '卅一']
    
    # 二十四节气数据（从0小寒起算，单位：分钟）
    TERM_INFO = [0, 21208, 42467, 63836, 85337, 107014, 128867, 150921, 173149, 195551, 218072, 240693,
                 263343, 285989, 308563, 331033, 353350, 375494, 397447, 419210, 440795, 462224, 483532, 504758]
    
    SOLAR_TERM = ['小寒', '大寒', '立春', '雨水', '惊蛰', '春分', '清明', '谷雨', '立夏', '小满', '芒种', '夏至',
                  '小暑', '大暑', '立秋', '处暑', '白露', '秋分', '寒露', '霜降', '立冬', '小雪', '大雪', '冬至']
    
    # 天干地支
    HEAVENLY_STEMS = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
    EARTHLY_BRANCHES = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
    ZODIAC = ['鼠', '牛', '虎', '兔', '龙', '蛇', '马', '羊', '猴', '鸡', '狗', '猪']
    
    # 简约黄历宜忌
    ALMANAC_DATA = {
        '01-01': {'yi': '祭祀，祈福，贺正月', 'ji': '诸事不宜'},
        '01-02': {'yi': '祭祀，祈福', 'ji': '出行，嫁娶'},
        '05-05': {'yi': '艾灸，放生', 'ji': '作灶，移徙'},
        '08-15': {'yi': '团圆，祭祀', 'ji': '诸事不宜'},
        '12-23': {'yi': '祭灶', 'ji': '迁徙，出行'},
    }
    
    INTER_FESTIVAL = {
        '01-01': '元旦', '02-14': '情人节', '03-08': '妇女节', '03-12': '植树节',
        '04-01': '愚人节', '05-01': '劳动节', '05-04': '五四青年节', '06-01': '儿童节',
        '07-01': '建党节', '08-01': '建军节', '09-03': '抗战胜利日', '09-10': '教师节',
        '10-01': '国庆节', '12-24': '平安夜', '12-25': '圣诞节',
    }
    
    DOMESTIC_FESTIVAL = {
        '01-01': '春节', '01-15': '元宵节', '02-02': '龙头节', '05-05': '端午节',
        '07-07': '七夕节', '07-15': '中元节', '08-15': '中秋节', '09-09': '重阳节',
        '10-01': '寒衣节', '10-15': '下元节', '12-08': '腊八节', '12-23': '小年',
    }
    
    @staticmethod
    def get_lunar_festival(month, day):
        """获取农历节假日"""
        key = f'{month:02d}-{day:02d}'
        return Calendar.DOMESTIC_FESTIVAL.get(key, '')
    
    @staticmethod
    def get_term(y, n):
        """获取某年的第n个节气为几日
        地球公转时间: 31556925974.7 毫秒
        1900年的正小寒点：01-06，1900年为基准点
        参数n: 第几个节气，从0小寒起算
        """
        from datetime import datetime, timedelta
        
        # 基准点：1900年1月6日
        base_date = datetime(1900, 1, 6)
        # termInfo的单位是分钟，计算距基准点的天数
        # 公式：天数 = (年数差*年平均毫秒数 + termInfo[n]分钟数) / (1000ms/s * 86400s/day)
        days_offset = (31556925974.7 * (y - 1900) + Calendar.TERM_INFO[n] * 60000) / 86400000
        term_date = base_date + timedelta(days=days_offset)
        
        return term_date.day
    
    @staticmethod
    def get_year_term(y, m, d):
        """获取某天的节气名称（如果有的话）"""
        month = 0
        for i in range(24):
            day = Calendar.get_term(y, i)
            if i % 2 == 0:
                month += 1
            if month == m and day == d:
                return Calendar.SOLAR_TERM[i]
        return ''
    
    @staticmethod
    def leap_month(y):
        """获取农历闰月（0表示无闰月）"""
        return Calendar.LUNAR_INFO[y - 1899] & 0x0f
    
    @staticmethod
    def leap_days(y):
        """获取农历闰月天数"""
        if Calendar.leap_month(y):
            return 30 if (Calendar.LUNAR_INFO[y - 1899] & 0x10000) else 29
        return 0
    
    @staticmethod
    def month_days(y, m):
        """获取农历某月天数"""
        return 30 if (Calendar.LUNAR_INFO[y - 1899] & (0x10000 >> m)) else 29
    
    @staticmethod
    def year_days(y):
        """获取农历某年总天数"""
        total = 0
        i = 0x08000
        while i > 0x00008:
            total += 30 if (Calendar.LUNAR_INFO[y - 1899] & i) else 29
            i >>= 1
        return total + Calendar.leap_days(y)
    
    @staticmethod
    def get_lunar_calendar(year, month, day):
        """获取农历日期 - 基准点：1899年2月10日"""
        from datetime import date
        
        # 基准点：1899年2月10日 (JavaScript new Date(1899,1,10))
        base_date = date(1899, 2, 10)
        cur_date = date(year, month, day)
        offset = (cur_date - base_date).days
        
        # 找农历年
        lunar_year = 1899
        for y in range(1899, 2101):
            days = Calendar.year_days(y)
            if offset - days < 1:
                lunar_year = y
                break
            offset -= days
        
        # 找农历月
        leap = Calendar.leap_month(lunar_year)
        is_leap = False
        is_leap_month = False
        
        lunar_month = 1
        for m in range(1, 13):
            # 处理闰月
            if leap > 0 and m == leap + 1 and not is_leap_month:
                is_leap_month = True
                m -= 1
                days = Calendar.leap_days(lunar_year)
            else:
                is_leap_month = False
                days = Calendar.month_days(lunar_year, m)
            
            if offset - days < 0:
                lunar_month = m
                break
            
            offset -= days
        
        lunar_day = offset + 1
        
        return {
            'year': lunar_year,
            'month': lunar_month,
            'day': lunar_day,
            'month_cn': Calendar.LUNAR_MONTH[lunar_month - 1],
            'day_cn': Calendar.LUNAR_DAY[lunar_day - 1] if lunar_day <= len(Calendar.LUNAR_DAY) else str(lunar_day),
        }
    
    @staticmethod
    def get_month_calendar(year, month):
        """获取某月的完整日历数据"""
        from datetime import date, timedelta
        
        view = []
        
        # 获取当月1号的星期几 (0=Mon, 6=Sun)
        first_day = date(year, month, 1)
        first_weekday = first_day.weekday()  # Python: 0=周一
        
        # 获取上个月和下个月
        if month == 1:
            p_year, p_month = year - 1, 12
        else:
            p_year, p_month = year, month - 1
        
        if month == 12:
            n_year, n_month = year + 1, 1
        else:
            n_year, n_month = year, month + 1
        
        # 计算天数
        def get_days_in_month(y, m):
            if m in [1, 3, 5, 7, 8, 10, 12]:
                return 31
            elif m in [4, 6, 9, 11]:
                return 30
            else:
                return 29 if ((y % 400 == 0) or (y % 4 == 0 and y % 100 != 0)) else 28
        
        c_days = get_days_in_month(year, month)
        p_days = get_days_in_month(p_year, p_month)
        
        # 需要补充的天数（HTML从周一开始，但我们需要从周日开始的数据）
        # Python weekday(): 0=Mon, 1=Tue, ..., 6=Sun
        # HTML weekday: 0=Sun, 1=Mon, ..., 6=Sat
        # 所以需要在前面补 first_weekday + 1 个上月的日期
        p_fill = first_weekday
        n_fill = 6 - ((p_fill + c_days) % 7)
        
        # 补充上月末尾
        for i in range(p_days - p_fill + 1, p_days + 1):
            lunar = Calendar.get_lunar_calendar(p_year, p_month, i)
            view.append({
                'year': p_year,
                'month': p_month,
                'day': i,
                'date': f'{p_year}-{p_month:02d}-{i:02d}',
                'lunar': lunar['day_cn'],  # 仅显示日期
                'other_month': True,
            })
        
        # 补充本月
        for i in range(1, c_days + 1):
            lunar = Calendar.get_lunar_calendar(year, month, i)
            solar_festival = Calendar.INTER_FESTIVAL.get(f'{month:02d}-{i:02d}', '')
            # 优先显示农历节假日，其次公历节假日，再次节气
            lunar_festival = Calendar.get_lunar_festival(lunar['month'], lunar['day'])
            solar_term = Calendar.get_year_term(year, month, i)
            view.append({
                'year': year,
                'month': month,
                'day': i,
                'date': f'{year}-{month:02d}-{i:02d}',
                'lunar': lunar['day_cn'],  # 仅显示日期
                'festival': lunar_festival or solar_festival or solar_term,  # 优先级：农历节假日 > 公历节假日 > 节气
                'other_month': False,
            })
        
        # 补充下月起始
        for i in range(1, n_fill + 1):
            lunar = Calendar.get_lunar_calendar(n_year, n_month, i)
            view.append({
                'year': n_year,
                'month': n_month,
                'day': i,
                'date': f'{n_year}-{n_month:02d}-{i:02d}',
                'lunar': lunar['day_cn'],  # 仅显示日期
                'other_month': True,
            })
        
        return view

    @staticmethod
    def get_china_era_year(y):
        """获取干支纪年"""
        # 甲子年为1900年
        num = (y - 1900) % 60
        return Calendar.HEAVENLY_STEMS[num % 10] + Calendar.EARTHLY_BRANCHES[num % 12]
    
    @staticmethod
    def get_zodiac(y):
        """获取生肖"""
        return Calendar.ZODIAC[(y - 1900) % 12]
    
    @staticmethod
    def get_china_era(year, month, day):
        """获取某天的天干地支"""
        lunar = Calendar.get_lunar_calendar(year, month, day)
        
        # 计算干支
        # 干支纪年
        era_year = Calendar.get_china_era_year(lunar['year'])
        zodiac = Calendar.get_zodiac(lunar['year'])
        
        return {
            'year': era_year,
            'zodiac': zodiac,
            'lunar_month': lunar['month'],
            'lunar_day': lunar['day'],
        }
    
    @staticmethod
    def get_almanac(lunar_month, lunar_day):
        """获取黄历宜忌（简约版）"""
        key = f'{lunar_month:02d}-{lunar_day:02d}'
        if key in Calendar.ALMANAC_DATA:
            return Calendar.ALMANAC_DATA[key]
        # 默认宜忌
        return {'yi': '祈福，祭祀', 'ji': '移徙，动土'}
