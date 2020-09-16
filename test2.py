import time

blocket_days = ['i måndags', 'i tisdags', 'i onsdags', 'i torsdags', 'i fredags', 'i lördags', 'i söndags']
blocket_months = ['jan.', 'feb.', 'mars', 'apr.', 'maj', 'juni', 'juli', 'aug.', 'sep.', 'okt.', 'nov.', 'dec.']

now = time.strptime("2 2021",  "%j %Y")

def test(timestamp_raw):
    timestamp_split = timestamp_raw.split(" ")
    time = timestamp_split[-1]
    time = time.split(":")
    hour = int(time[0])
    minute = int(time[1])
    year = now.tm_year
    print(timestamp_raw)
    print("Weekday now: " + blocket_days[weekday_now])
    
    for weekday_then, blocket_day in enumerate(blocket_days):
        if blocket_day not in timestamp_raw: continue
        
        delta_days = weekday_then - weekday_now
        if delta_days >= 0:
            delta_days -= 7

        year_day = now.tm_yday + delta_days
        if year_day <= 0:      
            year -= 1
            year_days = 365
            if year % 4 == 0:
                year_days += 1
            year_day += year_days
        return hour, minute, year_day, year
    
    month_day = int(timestamp_split[0])
    month = timestamp_split[1]
    month_number = blocket_months.index(month) + 1

    return hour, minute, month_day, month_number, year



for day in blocket_days:
    #timestamp_raw = day + " 15:45"
    timestamp_raw = "19 juni 19:43"
    weekday_now = now.tm_wday
    print(test(timestamp_raw))