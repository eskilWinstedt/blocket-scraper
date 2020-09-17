import time

blocket_days = ['i måndags', 'i tisdags', 'i onsdags', 'i torsdags', 'i fredags', 'i lördags', 'i söndags']
blocket_months = ['jan.', 'feb.', 'mars', 'apr.', 'maj', 'juni', 'juli', 'aug.', 'sep.', 'okt.', 'nov.', 'dec.']

#now = time.strptime("2 2021",  "%j %Y")
now = time.localtime()

def test(timestamp_raw):
    #now = time.strptime("2 2021",  "%j %Y")
    now = time.localtime()

    timestamp_split = timestamp_raw.split(" ")
    clock = timestamp_split[-1]
    clock = clock.split(":")
    hour = int(clock[0])
    minute = int(clock[1])
    year_day = now.tm_yday
    year = now.tm_year 
    print(timestamp_raw)
    
    if "idag" in timestamp_split or "igår" in timestamp_split:
        if "igår" in timestamp_split:
            year_day -= 1
            if year_day <= 0:   # year_day = 0 => last day of previous year
                year -= 1
                year_days = 365
                if year % 4 == 0:   # Leap year?
                    year_days += 1
                year_day += year_days
        datetime = time.strptime("{0}:{1} {2} {3}".format(hour, minute, year_day, year), "%H:%M %j %Y")
        return datetime

    # Weekday
    for weekday_then, blocket_day in enumerate(blocket_days):
        if blocket_day not in timestamp_raw: continue
        
        delta_days = weekday_then - weekday_now
        if delta_days >= 0:
            delta_days -= 7

        year_day += delta_days
        if year_day <= 0:      
            year -= 1
            year_days = 365
            if year % 4 == 0:
                year_days += 1
            year_day += year_days
        datetime = time.strptime("{0}:{1} {2} {3}".format(hour, minute, year_day, year), "%H:%M %j %Y")
        return datetime
    
    # Month day and month
    month_day = int(timestamp_split[0])
    month = timestamp_split[1]
    month_number = blocket_months.index(month) + 1

    # Has the datetime not occured yet this year? 
    if month_number > now.tm_mon:
        year -= 1
    elif month_number == now.tm_mon:
        if month_day > now.tm_mday:
            year -= 1
        elif month_day == now.tm_mday:
            if hour > now.tm_hour:
                year -= 1
            elif hour == now.tm_hour and minute > (now.tm_min + 3):     # Adding a bit of margin in case the system clock is out of tune with Blockets' servers
                year -= 1


    datetime = time.strptime("{0}:{1} {2} {3} {4}".format(hour, minute, month_day, month_number, year), "%H:%M %d %m %Y")
    return datetime


print(now)

#timestamp_raw = day + " 15:45"
timestamp_raw = "10 dec. 19:43"
weekday_now = now.tm_wday
print("Weekday now: " + blocket_days[weekday_now])
print(test(timestamp_raw))


timestamp_raw = "20 sep. 23:59"
weekday_now = now.tm_wday
print("Weekday now: " + blocket_days[weekday_now])
print(test(timestamp_raw))

timestamp_raw = "17 aug. 13:05"
weekday_now = now.tm_wday
print("Weekday now: " + blocket_days[weekday_now])
print(test(timestamp_raw))

timestamp_raw = "17 sep. 14:43"
weekday_now = now.tm_wday
print("Weekday now: " + blocket_days[weekday_now])
print(test(timestamp_raw))

timestamp_raw = "15 sep. 07:24"
weekday_now = now.tm_wday
print("Weekday now: " + blocket_days[weekday_now])
print(test(timestamp_raw))

timestamp_raw = "17 sep. 15:07"
weekday_now = now.tm_wday
print("Weekday now: " + blocket_days[weekday_now])
print(test(timestamp_raw))

timestamp_raw = "17 sep. 13:04"
weekday_now = now.tm_wday
print("Weekday now: " + blocket_days[weekday_now])
print(test(timestamp_raw))

timestamp_raw = "17 sep. 13:59"
weekday_now = now.tm_wday
print("Weekday now: " + blocket_days[weekday_now])
print(test(timestamp_raw))