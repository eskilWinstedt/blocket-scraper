import time

'''
'''


'''def list_elements_in_string(first_list, string):
    ''''''Checks if the first_list has any elements in the string''''''
    for index, element in first_list.items():
        if element in string:
            return index + 1
    return False'''


def days_since(weekday_then, weekday_now):
    '''weekday described in numbers from 0-6'''
    if weekday_now > weekday_then:
        return weekday_now - weekday_then
    else:
        return weekday_now - weekday_then + 7


class Toime:
    def __init__(self):
        pass
    def set_timestamp(self, raw_timestamp):
            '''Takes a timestamp from blocket in these formats: Idag 13:57 / Igår 03:34 / 
            I måndags hh:mm / 31 maj hh::m / 9 nov. 14:57.  Converts to time in seconds'''

            # Fetch the timestamp and convert to string
            raw_timestamp = self.soup.find('span', attrs={'class': 'PublishedTime__StyledTime-pjprkp-1'})
            raw_timestamp = self.soup_replace(raw_timestamp, 'Inlagd: <!-- -->')
            raw_timestamp = raw_timestamp.string

            timestamp_parts = raw_timestamp.split(' ')      # example: ['21', 'okt', '04:39]

            # Clock (hh:mm)
            clock = timestamp_parts[-1]     # '04:39'
            clock = clock.split(':')    # ['04', '39']
            clock = list(map(int, clock))   # [4, 39]
            print("clock: " + str(clock))

            # Current times
            seconds_now = time.time()  # Tinme since beginning of time in seconds
            time_now = time.localtime()   # A tuple with year, month, day, weekday etc.
            clock_now_seconds = time_now[3] * 3600 + time_now[4] * 60 + time_now[5]
            weekday_now = time_now[6]   # Weekday in numbers. Monday is 0
            
            seconds_now_no_clock = seconds_now - clock_now_seconds
            self.timestamp = seconds_now_no_clock + clock[0] * 3600 + clock[1] * 60 # Adding the hours and minutes from the ad
            
            blocket_days = ['i måndags', 'i tisdags', 'i onsdags', 'i torsdags', 'i fredags', 'i lördags', 'i söndags']
            blocket_months = ['jan.', 'feb.', 'mars', 'april', 'maj', 'juni', 'juli', 'aug.', 'sep.', 'okt.', 'nov.', 'dec.']
            
            if 'idag' in  raw_timestamp:    
                return
            elif 'igår' in raw_timestamp:
                self.timestamp -= 3600 * 24
            else:
                # Check for day
                for weekday_then, blocket_day in enumerate(blocket_days):
                    if blocket_day in raw_timestamp:
                        seconds_since = 3600 * 24 * days_since(weekday_then, weekday_now)
                        self.timestamp -= seconds_since
                        return
                
                # Check for month
                for month_index, blocket_month in enumerate(blocket_months):
                    if blocket_month in raw_timestamp:
                        month_number = month_index + 1
                        if month_number > time_now.tm_mon:
                            year = time_now.tm_year - 1
                        elif month_number < time_now.tm_mon:
                            year = time_now.tm_year
                        elif timestamp_parts[0] < time_now.tm_mday:     # ad_mday < mday_now ?
                            year = time_now.tm_year
                            # There are no blocket ads near one year old
                            print('WARNING!')
                            print('This blocket date was older than expected: raw_timestamp')
                        else:
                            year = time_now.tm_year - 1
                            # There are no blocket ads near one year old
                            print('WARNING!')
                            print('This blocket date was older than expected: raw_timestamp')
                        
                        month_day = int(timestamp_parts[0])
                        time_tuple = (year, month_number, month_day, clock[0], clock[1], 0, 0, 1, -1) # year, month, month_day, hours, minutes, seconds, week_day, year_day, daylight_savings (-1=auto).  Week_day and year_day doesn't make any difference 
                        self.timestamp = time.mktime(time_tuple)
                        return
                
                # The timestamp could not be set
                print('AN error has occurred.')
                print('This blocket date was not recognized: ' + raw_timestamp)
                self.timestamp = 0
yeah = Toime()

'''
while True:
    raw = input("timestamp: ")
    print(yeah.set_timestamp(raw))
'''

'''map = ['mån', 'tis', 'ons', 'tor', 'fre', 'lör', 'sön']
for now in range(0, 7):
    for then in range(0, 7):
        print('Idag är det ' + map[now] + '. Då var det ' + map[then] + '. Det är ' + str(days_since(then, now)) + ' dagar sedan.')
'''

mapen = ['i måndags', 'i tisdags', 'i onsdags', 'i torsdags', 'i fredags', 'i lördags', 'i söndags', 'BANANA']
for times in mapen:
    print(times + ' 19:26')
    print(time.localtime(yeah.set_timestamp(times + ' 19:26')))
print(time.localtime(yeah.set_timestamp('9 nov.' + ' 19:26')))
print(time.localtime(yeah.set_timestamp('30 juli' + ' 19:26')))
print(time.localtime(yeah.set_timestamp('29 aug.' + ' 19:26')))
print(time.localtime(yeah.set_timestamp('1 jan.' + ' 19:26')))
print(time.localtime(yeah.set_timestamp('11 dec.' + ' 19:26')))
