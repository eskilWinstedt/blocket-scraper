
import time

'''def list_elements_in_string(first_list, string):
    ''''''Checks if the first_list has any elements in the string''''''
    for index, element in first_list.items():
        if element in string:
            return index + 1
    return False'''


def days_since(weekday_then, weekday_now):
    '''weekday described in numbers from 0-6'''
    if weekday_now >= weekday_then:
        return weekday_now - weekday_then
    else:
        return weekday_now - weekday_then + 7

def set_timestamp(times):
        # smalldatetime	YYYY-MM-DD hh:mm:ss
        '''raw_timestamp = self.soup.find('span', attrs={'class': 'PublishedTime__StyledTime-pjprkp-1'})
        raw_timestamp = self.soup_replace(raw_timestamp, 'Inlagd: <!-- -->')
        raw_timestamp = raw_timestamp.string'''
        raw_timestamp = times
        timestamp_split = raw_timestamp.split(' ') # Splits into ['21', 'okt', '04:39]
        clock = timestamp_split[-1]
        clock = clock.split(':')       # '4:39' ---> ['4', '39']
        clock = list(map(int, clock)) # ['4', '39'] ---> [4, 39]
        time_in_seconds = time.time()   # Current time in seconds
        time_now = time.gmtime()   # Current time. A tuple with year, mon, day, weekday etc.
        weekday_now = time_now[6]   # Weekday in numbers where monday is 0
        time_no_clock = time_in_seconds - time_now[3] * 3600 - time_now[4] * 60 - time_now[5]     # Removes the hours, minutes and seconds from the time right now
        timestamp = time_no_clock + clock[0] * 3600 + clock[1] * 60 # Adding the hours and minutes from the ad
        blocket_days = ['i måndags', 'i tisdags', 'i onsdags', 'i torsdags', 'i fredags', 'i lördags', 'i söndags']
        blocket_months = ['jan', 'feb', 'mars', 'april', 'maj', 'juni', 'juli', 'aug', 'sep', 'okt', 'nov', 'dec']
        if 'idag' in  raw_timestamp:    
            return timestamp
        elif 'igår' in raw_timestamp:
            timestamp -= 3600 * 24 # Removes one day
        else:
            for weekday_then, blocket_day in enumerate(blocket_days):
                if blocket_day in raw_timestamp:
                    return timestamp - 3600 * 24 * days_since(weekday_then, weekday_now)  # Removes days in seconds depending on
            for month, blocket_month in enumerate(blocket_months):
                if blocket_month in raw_timestamp:
                    month_day = int(timestamp_split[0])
                    time_tuple = (2019, month + 1, month_day, clock[0], clock[1], 0, 0, 1, -1) # year, month, month_day, hours, minutes, seconds, week_day, year_day, daylight_savings (-1=auto).  Week_day and year_day doesn't make any difference 
                    return time.mktime(time_tuple)
            print('AN error has occurred.')
            print('This blocket date was not recognized: ' + raw_timestamp)

'''
while True:
    raw = input("timestamp: ")
    print(set_timestamp(raw))
'''

'''map = ['mån', 'tis', 'ons', 'tor', 'fre', 'lör', 'sön']
for now in range(0, 7):
    for then in range(0, 7):
        print('Idag är det ' + map[now] + '. Då var det ' + map[then] + '. Det är ' + str(days_since(then, now)) + ' dagar sedan.')
'''

mapen = ['i måndags', 'i tisdags', 'i onsdags', 'i torsdags', 'i fredags', 'i lördags', 'i söndags', 'BANANA']
for times in mapen:
    print(times + ' 19:26')
    print(time.gmtime(set_timestamp(times + ' 19:26')))
print(time.gmtime(set_timestamp('9 nov' + ' 19:26')))
print(time.gmtime(set_timestamp('30 juli' + ' 19:26')))
print(time.gmtime(set_timestamp('29 feb' + ' 19:26')))
print(time.gmtime(set_timestamp('1 jan' + ' 19:26')))
print(time.gmtime(set_timestamp('11 dec' + ' 19:26')))
