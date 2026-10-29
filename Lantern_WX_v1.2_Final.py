#!/usr/bin/env python3
# coding: utf-8

# lantern-wx
#######################
# User Definition Area:

# To display imperial units, remove the hash mark (#) before the line with imperial text in it
unit_type = 'metric'
unit_type = 'imperial'

# Set the API_key to a key registered under your name at openweathermap.org:
API_key = [INSERT YOUR API KEY HERE]

# If no grid is specified or of the wrong format, then a default grid will be used.
# Set the default maidenhead gridsquare here:
default_grid = 'EN35MH'

# To enable email forwarding, uncomment ENABLE_EMAIL = True and add email account information below.
ENABLE_EMAIL = False
#ENABLE_EMAIL = True
MSG_EMAIL_NOTIFICATION = False
#MSG_EMAIL_NOTIFICATION = True
# SMTP email server account information:
email_address = 'Your_email_address'
email_server = 'Your_SMTP_email_server'
email_password = 'Your_SMTP_email_server_password'
message_email_address = 'email_address_to_receive_messages'
# Message beacon settings
ENABLE_MESSAGE_BEACON_1 = False # Enable by replacing False with True
message_period_1 = 121 # Number of minutes between transmissions
message_file_path_1 = 'qso_party.txt' # Path and file name of message
ENABLE_MESSAGE_BEACON_2 = False # Enable by replacing False with True
message_period_2 = 165 # Number of minutes between transmissions
message_file_path_2 = 'help_test.txt' # Path and file name of message
ENABLE_MESSAGE_BEACON_3 = False # Enable by replacing False with True
message_period_3 = 159 # Number of minutes between transmissions
message_file_path_3 = 'wxsnr.txt' # Path and file name of message#
ENABLE_MESSAGE_BEACON_4 = False # Enable by replacing False with True
message_period_4 = 60 # Number of minutes between transmissions
message_file_path_4 = 'heartbeat.txt' # Path and file name of message
ENABLE_MESSAGE_BEACON_5 = False # Enable by replacing False with True
message_period_5 = 243 # Number of minutes between transmissions
message_file_path_5 = 'emcomm_services.txt' # Path and file name of message
# Mouse click simulator
ENABLE_MOUSE_CLICK_SIMULATOR = False # Enable by replacing False with True
mouse_click_period = 240 # Number of minutes between mouse clicks

# End User Definition Area
##################################

import time
import math
import datetime
import json
from js8net import *
import re
import requests
import maidenhead as mh
#import os
#import mimetypes
import smtplib
from email.message import EmailMessage
import threading
from pynput import mouse
import pyautogui as pg

def on_click(x, y, button, pressed):
    global xvar
    global yvar
    if button == mouse.Button.left:
        xvar = x
        yvar = y
        return False

def message_beacon(path_to_file):
    message_file = open(path_to_file)
    message_content = message_file.read()
    send_message(message_content)
    message_file.close()
        
def msg_email_notification(sender_callsign, operator_callsign, operator_email_address, body_text, SMTP_email_address, SMTP_email_server, SMTP_email_password):
    mail_server = smtplib.SMTP_SSL(SMTP_email_server)
    sender = SMTP_email_address
    recipient = operator_email_address
    password = SMTP_email_password
    message = EmailMessage()
    message['From'] = sender
    message['To'] = recipient
    message['Subject'] = 'JS8Call message from ' + sender_callsign + ' to ' + operator_callsign
    footer = '\n\nEnd of message.'
    full_body_text = 'JS8Call message from ' + sender_callsign + '\n\nBegin message:\n\n' + body_text + footer
    try:
# login and send email
        message.set_content(full_body_text)
        mail_server.login(sender, password)
        mail_server.send_message(message)
        mail_server.quit()
        print('Message sent to station operator at ' + operator_email_address + ' by email.')
        transcript_file = 'transcript.txt'
        with open(transcript_file, 'a') as file:
            file.write('\n' + sender_callsign + ': ' + operator_callsign  + ' Message sent to station operator ' + operator_email_address + ' by email.')
    except Exception as e:
        print('Error: ')
        print(e)
        print('\nSorry, message forwarded by email did not go through.')
        transcript_file = 'transcript.txt'
        with open(transcript_file, 'a') as file:
            file.write('\n' + sender_callsign + ': ' + operator_callsign + '\nSorry, message forwarded by email did not go through.')
 
def email_push(request_callsign, sender_callsign, recipient_email_address, body_text, SMTP_email_address, SMTP_email_server, SMTP_email_password):
    mail_server = smtplib.SMTP_SSL(SMTP_email_server)
    sender = SMTP_email_address
    recipient = recipient_email_address
    password = SMTP_email_password
    message = EmailMessage()
    message['From'] = sender
    message['To'] = recipient
    message['Subject'] = 'Email forwarded from amateur radio operator ' + request_callsign
    footer = '\n\nEnd of message. \n\nThis email was received as a radio signal and may contain errors. Do not reply to this email. This email address is not monitored.'
    full_body_text = 'Forwarded message from ' + request_callsign + '\n\nBegin message:\n\n' + body_text + footer
    try:
# login and send email
        message.set_content(full_body_text)
        mail_server.login(sender, password)
        mail_server.send_message(message)
        mail_server.quit()
        print('Email sent to ' + recipient_email_address + '.')
        send_inbox_message(request_callsign, 'Email sent to ' + recipient_email_address)
        transcript_file = 'transcript.txt'
        with open(transcript_file, 'a') as file:
            file.write('\n' + sender_callsign + ': ' + request_callsign  + ' MSG Email sent to ' + recipient)
    except Exception as e:
        send_inbox_message(request_callsign, 'Sorry, email to ' + recipient_email_address + ' did not go through.') 
        print('Error: ')
        print(e)
        print('\nSorry, email to ' + recipient_email_address + ' did not go through.')
        transcript_file = 'transcript.txt'
        with open(transcript_file, 'a') as file:
            file.write('\n' + sender_callsign + ': ' + request_callsign + ' MSG Sorry, email to ' + recipient + ' did not go through.')
        
def openweathermap_wind_api_call(forecast_day, user_API_key, display_unit_type, sender_callsign, request_callsign, latitude, longitude, coordinate_check):
    try:
# Build url for openweathermap request
        base_url = "http://api.openweathermap.org/data/2.5/forecast?"
        Final_url = base_url + "appid=" + user_API_key + "&lat=" + str(latitude) + "&lon=" + str(longitude) + "&units=" + display_unit_type 
# Get openweathermap json with url
        forecast_json = requests.get(Final_url).json()
    except Exception as e:
        print(e)
# Select a forecast period in the desired forecast_day (8 forecast periods per day)
    forecast_period = int(forecast_day * 8)
# Make sure the forecast period is within the range of 0 to 39
    if(forecast_period > 39):
        forecast_period = 39
    if(forecast_period < 0):
        forecast_period = 0
# Pull date and time string out of json using forecast period
    dt_txt = forecast_json['list'][forecast_period]['dt_txt']
# Split out the date from the date - time string
    day_of_interest = dt_txt.split()[0]
# Set display units
    if (display_unit_type == 'imperial'):
        temp_unit = ' F'
        speed_unit = ' mph'
    if (display_unit_type == 'metric'):
        temp_unit = ' C'
        speed_unit = ' m/s'
# Print header
# Build WIND_FORECAST tx_string Header Needed City Name in WIND? output
    city_name = str(forecast_json['city']['name'])
    if coordinate_check:
        city_name = str(forecast_json['city']['name']) +'\n' + str(latitude) + ', ' + str(longitude)
    tx_string = ('Wind Forecast for ' + city_name + '\n\n')
# Go through data in forecast_json, and select data with requested day of interest
    for count in range(0, 40, 2):
        date_time = forecast_json['list'][count]['dt_txt']
        try:
# If the data is of the correct date, print it out, then continue loop through range
            if day_of_interest == date_time.split()[0]:
                tx_string += date_time[:-3] + '\n'
                tx_string += 'press ' + format_pressure(forecast_json['list'][count]['main']['pressure'], display_unit_type) + '\n'
                tx_string += 'wind ' + str(round(forecast_json['list'][count]['wind']['speed'])) + speed_unit + '\n'
                tx_string += 'gust ' + str(round(forecast_json['list'][count]['wind']['gust'])) + speed_unit + '\n'
                tx_string += 'dir ' + str(forecast_json['list'][count]['wind']['deg']) + ' deg' + '\n\n'
        except Exception as e:
            print(e)
    print(sender_callsign + ': ' + request_callsign + ' MSG' + '\n' + tx_string)
    send_inbox_message(request_callsign, tx_string)
    transcript_file = 'transcript.txt'
    with open(transcript_file, 'a') as file:
        file.write('\n' + my_call + ': ' + request_callsign + ' MSG ' +'\n' + tx_string + '\n')

def openweathermap_wx_api_call(forecast_day, user_API_key, display_unit_type, sender_callsign, request_callsign, latitude, longitude, coordinate_check):
# Convert from requested day to number of 3 hour weather periods as provided in API
    forecast_period = int(forecast_day * 8)
    if(forecast_period > 39):
        forecast_period = 39
    if(forecast_period < 0):
        forecast_period = 0
# Set up unit display type    
    if(display_unit_type == 'metric'):
        temp_unit = 'C'
        wind_unit = 'm/s'
    if(display_unit_type == 'imperial'):
        temp_unit = 'F'
        wind_unit = 'mph'
# Check for NOAA weather alerts
    try:
        NOAA_url = 'https://api.weather.gov/alerts/active?point=' + str(latitude) + ',' + str(longitude)
        NOAA_alert = requests.get(NOAA_url).json()
        alert_message = ''
        alert_message = NOAA_alert['features'][0]['properties']['event']
        alert_message = '\nALERT NOW: ' + alert_message
    except:
        pass
# Connect to Openopenweathermap.org API and get json dictionary
    base_url = "http://api.openweathermap.org/data/2.5/forecast?"
    Final_url = base_url + "appid=" + user_API_key + "&lat=" + str(latitude) + "&lon=" + str(longitude) + "&units=" + unit_type 
    try:
        forecast_json = requests.get(Final_url).json()
    except Exception as e:
        print(e)
# Build WX_FORECAST
    city_name = str(forecast_json['city']['name'])
    if coordinate_check:
        city_name = str(forecast_json['city']['name']) +'\n' + str(latitude) + ', ' + str(longitude)
# Pull date and time string out of json
    dt_txt = forecast_json['list'][forecast_period]['dt_txt']
# Split date separate from date - time
    forecast_date = dt_txt.split()[0]
    display_date = forecast_date
# If required, convert strings to ints
    try:
        maximum_temp_int = int(get_maximum_temp_from_day(forecast_date, forecast_json))
        minimum_temp_int = int(get_minimum_temp_from_day(forecast_date, forecast_json))
        maximum_wind_speed_int = int(get_maximum_wind_speed_from_day(forecast_date, forecast_json))
        maximum_gust_speed_int = int(get_maximum_gust_speed_from_day(forecast_date, forecast_json))
    except Exception as e:
        print(e)
# Short description of weather
    description = forecast_json['list'][forecast_period]['weather'][0]['description']
# Calculate the maximum temperature of the day
    maximum_temp =  'max ' + str(maximum_temp_int)  + ' ' + temp_unit 
# Calculate the minimum temperature in the day
    minimum_temp =  'min ' + str(minimum_temp_int)  + ' ' + temp_unit 
# Barometric Pressure
    pressure = 'press ' + format_pressure(forecast_json['list'][forecast_period]['main']['pressure'], display_unit_type)
# Calculate maximum wind speed of the day
    maximum_wind_speed = 'wind ' + str(maximum_wind_speed_int) + ' ' + wind_unit
# Calculate maximum gust of day
    maximum_gust_speed = 'gust ' + str(maximum_gust_speed_int) + ' ' + wind_unit
# Wind direction at time of forecast from compass reading
    wind_deg = 'wind dir ' + str(forecast_json['list'][forecast_period]['wind']['deg']) + ' deg'
# Output to send for transmission
    try:
        wx_forecast = alert_message + '\nForecast for ' + city_name + '\n' + display_date + '\n' + description + '\n' + maximum_temp + '\n' + minimum_temp + '\n' + pressure + '\n' + maximum_wind_speed + '\n' + maximum_gust_speed + '\n' + wind_deg + '\n'
        print(sender_callsign + ': ' + request_callsign + ' MSG' + wx_forecast)
        send_inbox_message(request_callsign, wx_forecast)
        transcript_file = 'transcript.txt'
        with open(transcript_file, 'a') as file:
            file.write('\n' + my_call + ': ' + request_callsign + ' MSG' + wx_forecast + '\n')
    except Exception as e:
        print(e)

def get_maximum_temp_from_day(day_of_interest, forecast_data):
# Written for openopenweathermap API data
    new_max_temp = 0
# Go through data with day of interest, and select the maximum temp
    for count in range(0, 40, 1):
        dt_txt_iteration = forecast_data['list'][count]['dt_txt']
        if day_of_interest == dt_txt_iteration.split()[0]:
            variable_value = int(forecast_data['list'][count]['main']['temp_max'])
            if variable_value > new_max_temp:
                new_max_temp = variable_value
    return new_max_temp
    
def get_minimum_temp_from_day(day_of_interest, forecast_data):
# Written for openopenweathermap API data
    new_min_temp = 1000
# Go through data with day of interest, and select the minimum temp
    for count in range(0, 40, 1):
        dt_txt_iteration = forecast_data['list'][count]['dt_txt']
        if day_of_interest == dt_txt_iteration.split()[0]:
            variable_value = int(forecast_data['list'][count]['main']['temp_min'])
            if variable_value < new_min_temp:
                new_min_temp = variable_value
    return new_min_temp

def get_maximum_wind_speed_from_day(day_of_interest, forecast_data):
# Written for openopenweathermap API data
    new_max_wind_speed = 0
# Go through data from day of interest, select the highest wind speed
    for count in range(0, 40, 1):
        dt_txt_iteration = forecast_data['list'][count]['dt_txt']
        if day_of_interest == dt_txt_iteration.split()[0]:
            variable_value = int(forecast_data['list'][count]['wind']['speed'])
            if variable_value > new_max_wind_speed:
                new_max_wind_speed = variable_value
    return new_max_wind_speed
   
def get_maximum_gust_speed_from_day(day_of_interest, forecast_data):
# Written for openopenweathermap API data
    new_max_gust_speed = 0
# Go through data from day of interest, select the highest wind gust
    for count in range(0, 40, 1):
        dt_txt_iteration = forecast_data['list'][count]['dt_txt']
        if day_of_interest == dt_txt_iteration.split()[0]:
            variable_value = int(forecast_data['list'][count]['wind']['gust'])
            if variable_value > new_max_gust_speed:
                new_max_gust_speed = variable_value
    return new_max_gust_speed

def format_pressure(hpa, display_unit_type):
    # OpenWeatherMap always returns pressure in hPa
    if display_unit_type == 'imperial':
        return str(round(float(hpa) * 0.02953, 2)) + ' inHg'
    return str(hpa) + ' hPa'

def brief_sky_code(cloud_percent):
    if cloud_percent <= 10:
        return 'CLR'
    if cloud_percent <= 30:
        return 'FEW'
    if cloud_percent <= 60:
        return 'SCT'
    if cloud_percent <= 87:
        return 'BKN'
    return 'OVC'

def brief_present_weather(day_entries):
    group_rank = {2: 4, 6: 3, 5: 2, 3: 1, 7: 0}
    best_id = None
    best_key = None
    for entry in day_entries:
        for w in entry['weather']:
            wid = w['id']
            group = wid // 100
            if group not in group_rank:
                continue
            key = (group_rank[group], wid % 10)
            if best_key is None or key > best_key:
                best_key = key
                best_id = wid
    if best_id is None:
        return ''
    group = best_id // 100
    if best_id == 511:
        return 'FZRA'
    if best_id in (611, 612, 613):
        return 'PL'
    if best_id in (615, 616):
        return 'RASN'
    if group == 2:
        return 'TS'
    if group == 7:
        return {701: 'BR', 711: 'FU', 721: 'HZ', 731: 'DU', 741: 'FG', 751: 'SA', 761: 'DU', 762: 'VA', 771: 'SQ', 781: 'FC'}.get(best_id, '')
    code = {3: 'DZ', 5: 'RA', 6: 'SN'}[group]
    digit = best_id % 10
    if digit == 0:
        return '-' + code
    if digit >= 2:
        return '+' + code
    return code

def brief_alert_remark(latitude, longitude):
    try:
        alert_url = 'https://api.weather.gov/alerts/active?point=' + str(latitude) + ',' + str(longitude)
        alerts = requests.get(alert_url, headers={'User-Agent': 'JS8CallWXServer'}, timeout=10).json()
        best = None
        for feature in alerts['features']:
            words = feature['properties']['event'].upper().split()
            if len(words) < 2:
                continue
            priority = {'WARNING': 0, 'WATCH': 1, 'ADVISORY': 2}.get(words[-1])
            if priority is None:
                continue
            if best is None or priority < best[0]:
                best = (priority, words[-1] + ': ' + ' '.join(words[:-1]))
        if best:
            return 'RMK ' + best[1]
    except Exception as e:
        print(e)
    return ''

def openweathermap_brief_api_call(forecast_day, user_API_key, display_unit_type, sender_callsign, request_callsign, latitude, longitude, location_label):
    try:
        forecast_period = max(0, min(39, int(forecast_day * 8)))
        base_url = "http://api.openweathermap.org/data/2.5/forecast?"
        Final_url = base_url + "appid=" + user_API_key + "&lat=" + str(latitude) + "&lon=" + str(longitude) + "&units=" + display_unit_type
        forecast_json = requests.get(Final_url, timeout=10).json()
        forecast_date = forecast_json['list'][forecast_period]['dt_txt'].split()[0]
        day_entries = [e for e in forecast_json['list'] if e['dt_txt'].split()[0] == forecast_date]
        # Wind: direction from first period of the day, speed and gust are the day's maximums
        direction = int(round(day_entries[0]['wind']['deg'] / 10.0)) * 10
        if direction == 0:
            direction = 360
        wind_speed = int(round(max(e['wind']['speed'] for e in day_entries)))
        gusts = [e['wind']['gust'] for e in day_entries if 'gust' in e['wind']]
        wind = '%03d%02d' % (direction, wind_speed)
        if wind_speed == 0:
            wind = '00000'
        elif gusts and int(round(max(gusts))) > wind_speed:
            wind += 'G%02d' % int(round(max(gusts)))
        wind += 'mph' if display_unit_type == 'imperial' else 'mps'
        present_weather = brief_present_weather(day_entries)
        sky = brief_sky_code(sum(e['clouds']['all'] for e in day_entries) / float(len(day_entries)))
        max_temp = int(round(max(e['main']['temp_max'] for e in day_entries)))
        min_temp = int(round(min(e['main']['temp_min'] for e in day_entries)))
        hpa = float(forecast_json['list'][forecast_period]['main']['pressure'])
        if display_unit_type == 'imperial':
            pressure = 'A%04d' % round(hpa * 2.953)
        else:
            pressure = 'Q%04d' % round(hpa)
        remark = ''
        if forecast_day == 0:
            remark = brief_alert_remark(latitude, longitude)
        parts = [forecast_date, location_label, wind, present_weather, sky, '%d/%d' % (max_temp, min_temp), pressure, remark]
        brief = ' '.join(p for p in parts if p)
        print(sender_callsign + ': ' + request_callsign + ' MSG ' + brief)
        return brief
    except Exception as e:
        print(e)
        return None

def moon_position(jd):
    # Low-precision lunar position (good to roughly 0.3 degrees):
    # ecliptic longitude, ecliptic latitude, horizontal parallax (all degrees)
    T = (jd - 2451545.0) / 36525.0
    r = math.pi / 180.0
    lon = (218.32 + 481267.881 * T
           + 6.29 * math.sin(r * (135.0 + 477198.87 * T))
           - 1.27 * math.sin(r * (259.3 - 413335.36 * T))
           + 0.66 * math.sin(r * (235.7 + 890534.22 * T))
           + 0.21 * math.sin(r * (269.9 + 954397.74 * T))
           - 0.19 * math.sin(r * (357.5 + 35999.05 * T))
           - 0.11 * math.sin(r * (186.5 + 966404.03 * T)))
    lat = (5.13 * math.sin(r * (93.3 + 483202.02 * T))
           + 0.28 * math.sin(r * (228.2 + 960400.89 * T))
           - 0.28 * math.sin(r * (318.3 + 6003.15 * T))
           - 0.17 * math.sin(r * (217.6 - 407332.21 * T)))
    par = (0.9508
           + 0.0518 * math.cos(r * (135.0 + 477198.87 * T))
           + 0.0095 * math.cos(r * (259.3 - 413335.36 * T))
           + 0.0078 * math.cos(r * (235.7 + 890534.22 * T))
           + 0.0028 * math.cos(r * (269.9 + 954397.74 * T)))
    return lon % 360.0, lat, par

def moon_sun_longitude(jd):
    # Low-precision ecliptic longitude of the sun, in degrees
    n = jd - 2451545.0
    mean_lon = 280.460 + 0.9856474 * n
    g = math.radians(357.528 + 0.9856003 * n)
    return (mean_lon + 1.915 * math.sin(g) + 0.020 * math.sin(2 * g)) % 360.0

def moon_altitude_margin(jd, lat_deg, lon_deg):
    # Moon altitude minus the altitude at which it counts as risen. Crosses zero at moonrise and moonset.
    lam, beta, par = moon_position(jd)
    n = jd - 2451545.0
    eps = math.radians(23.439 - 0.0000004 * n)
    lam = math.radians(lam)
    beta = math.radians(beta)
    x = math.cos(beta) * math.cos(lam)
    y = math.cos(beta) * math.sin(lam) * math.cos(eps) - math.sin(beta) * math.sin(eps)
    z = math.cos(beta) * math.sin(lam) * math.sin(eps) + math.sin(beta) * math.cos(eps)
    ra = math.atan2(y, x)
    dec = math.asin(z)
    gmst = (280.46061837 + 360.98564736629 * n) % 360.0
    hour_angle = math.radians(gmst + lon_deg) - ra
    phi = math.radians(lat_deg)
    sin_alt = math.sin(phi) * math.sin(dec) + math.cos(phi) * math.cos(dec) * math.cos(hour_angle)
    alt = math.degrees(math.asin(max(-1.0, min(1.0, sin_alt))))
    return alt - (0.7275 * par - 0.5667)

def moon_rise_set(date_utc, lat_deg, lon_deg):
    # Returns (rise, set) as minutes after 00:00 UTC on date_utc, or None if it does not happen that day
    jd0 = 2440587.5 + (date_utc.toordinal() - datetime.date(1970, 1, 1).toordinal())
    step = 1.0 / 144.0
    rise = None
    set_ = None
    prev = moon_altitude_margin(jd0, lat_deg, lon_deg)
    for k in range(1, 145):
        lo = jd0 + (k - 1) * step
        hi = jd0 + k * step
        cur = moon_altitude_margin(hi, lat_deg, lon_deg)
        going_up = prev < 0 <= cur
        going_down = prev >= 0 > cur
        if (going_up and rise is None) or (going_down and set_ is None):
            for i in range(30):
                mid = (lo + hi) / 2.0
                value = moon_altitude_margin(mid, lat_deg, lon_deg)
                if (value >= 0) == going_up:
                    hi = mid
                else:
                    lo = mid
            minutes = ((lo + hi) / 2.0 - jd0) * 1440.0
            if going_up:
                rise = minutes
            else:
                set_ = minutes
        prev = cur
    return rise, set_

def moon_illumination(jd):
    # Returns (percent of the disc lit, moon-sun angle in degrees: 0 = new, 90 = first quarter, 180 = full)
    lam, beta, par = moon_position(jd)
    angle = (lam - moon_sun_longitude(jd)) % 360.0
    cos_elong = math.cos(math.radians(beta)) * math.cos(math.radians(angle))
    return (1.0 - cos_elong) / 2.0 * 100.0, angle

def moon_phase_name(illumination, angle):
    # Named by how much of the disc is lit, like most almanacs. angle < 180 means the moon is waxing.
    waxing = angle < 180.0
    if illumination < 3.0:
        return 'NEW'
    if illumination > 97.0:
        return 'FULL'
    if 46.0 <= illumination <= 54.0:
        return 'FIRST QUARTER' if waxing else 'LAST QUARTER'
    shape = 'CRESCENT' if illumination < 50.0 else 'GIBBOUS'
    return ('WAXING ' if waxing else 'WANING ') + shape

def moon_clock(minutes):
    if minutes is None:
        return '--'
    m = min(1439, int(round(minutes)))
    return '%02d%02d' % (m // 60, m % 60)

def moon_report(forecast_day, sender_callsign, request_callsign, latitude, longitude, location_label):
    # One-line moon report. Works fully offline. All times are UTC.
    try:
        date_utc = datetime.datetime.now(datetime.timezone.utc).date() + datetime.timedelta(days=int(forecast_day))
        lat = float(latitude)
        lon = float(longitude)
        rise, set_ = moon_rise_set(date_utc, lat, lon)
        noon_jd = 2440587.5 + (date_utc.toordinal() - datetime.date(1970, 1, 1).toordinal()) + 0.5
        illumination, angle = moon_illumination(noon_jd)
        report = ' '.join([date_utc.isoformat(), location_label, 'MOON', 'R' + moon_clock(rise), 'S' + moon_clock(set_), 'UTC', 'ILL%d%%' % round(illumination), moon_phase_name(illumination, angle)])
        print(sender_callsign + ': ' + request_callsign + ' MSG ' + report)
        return report
    except Exception as e:
        print(e)
        return None

def sun_altitude_margin(jd, lat_deg, lon_deg):
    # Sun altitude minus the altitude at which it counts as risen (-0.833 degrees: refraction plus the sun's radius).
    # Crosses zero at sunrise and sunset.
    n = jd - 2451545.0
    lam = math.radians(moon_sun_longitude(jd))
    eps = math.radians(23.439 - 0.0000004 * n)
    ra = math.atan2(math.cos(eps) * math.sin(lam), math.cos(lam))
    dec = math.asin(math.sin(eps) * math.sin(lam))
    gmst = (280.46061837 + 360.98564736629 * n) % 360.0
    hour_angle = math.radians(gmst + lon_deg) - ra
    phi = math.radians(lat_deg)
    sin_alt = math.sin(phi) * math.sin(dec) + math.cos(phi) * math.cos(dec) * math.cos(hour_angle)
    alt = math.degrees(math.asin(max(-1.0, min(1.0, sin_alt))))
    return alt + 0.833

def sun_rise_set(date_utc, lat_deg, lon_deg):
    # Returns (rise, set) as minutes after 00:00 UTC on date_utc, or None if it does not happen that day
    jd0 = 2440587.5 + (date_utc.toordinal() - datetime.date(1970, 1, 1).toordinal())
    step = 1.0 / 144.0
    rise = None
    set_ = None
    prev = sun_altitude_margin(jd0, lat_deg, lon_deg)
    for k in range(1, 145):
        lo = jd0 + (k - 1) * step
        hi = jd0 + k * step
        cur = sun_altitude_margin(hi, lat_deg, lon_deg)
        going_up = prev < 0 <= cur
        going_down = prev >= 0 > cur
        if (going_up and rise is None) or (going_down and set_ is None):
            for i in range(30):
                mid = (lo + hi) / 2.0
                value = sun_altitude_margin(mid, lat_deg, lon_deg)
                if (value >= 0) == going_up:
                    hi = mid
                else:
                    lo = mid
            minutes = ((lo + hi) / 2.0 - jd0) * 1440.0
            if going_up:
                rise = minutes
            else:
                set_ = minutes
        prev = cur
    return rise, set_

def sun_report(forecast_day, sender_callsign, request_callsign, latitude, longitude, location_label):
    # One-line sun report. Works fully offline. All times are UTC.
    try:
        date_utc = datetime.datetime.now(datetime.timezone.utc).date() + datetime.timedelta(days=int(forecast_day))
        lat = float(latitude)
        lon = float(longitude)
        rise, set_ = sun_rise_set(date_utc, lat, lon)
        if rise is None and set_ is None:
            noon_jd = 2440587.5 + (date_utc.toordinal() - datetime.date(1970, 1, 1).toordinal()) + 0.5
            if sun_altitude_margin(noon_jd, lat, lon) >= 0:
                times = 'UP ALL DAY'
            else:
                times = 'DOWN ALL DAY'
        else:
            times = 'R' + moon_clock(rise) + ' S' + moon_clock(set_) + ' UTC'
        report = ' '.join([date_utc.isoformat(), location_label, 'SUN', times])
        print(sender_callsign + ': ' + request_callsign + ' MSG ' + report)
        return report
    except Exception as e:
        print(e)
        return None

def space_fetch(path, want_json):
    # Download one NOAA Space Weather Prediction Center product. Raises an error if it fails.
    response = requests.get('https://services.swpc.noaa.gov/' + path, timeout=10)
    response.raise_for_status()
    if want_json:
        return response.json()
    return response.text

def space_latest_flux():
    data = space_fetch('products/summary/10cm-flux.json', True)
    if isinstance(data, list):
        data = data[0]
    return int(round(float(data['flux'])))

def space_latest_kp():
    rows = space_fetch('products/noaa-planetary-k-index.json', True)
    for row in reversed(rows):
        try:
            if isinstance(row, dict):
                return float(row['Kp'])
            return float(row[1])
        except (ValueError, KeyError, IndexError, TypeError):
            continue
    raise ValueError('no Kp value found')

def space_outlook_table():
    # Returns {date: (10.7 cm flux, largest Kp)} from the 27-day outlook
    months = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}
    text = space_fetch('text/27-day-outlook.txt', False)
    table = {}
    for line in text.splitlines():
        parts = line.split()
        if len(parts) == 6 and parts[0].isdigit() and parts[1] in months and parts[2].isdigit():
            try:
                table[datetime.date(int(parts[0]), months[parts[1]], int(parts[2]))] = (int(parts[3]), int(parts[5]))
            except ValueError:
                continue
    return table

def space_predicted_ssn(date_utc):
    # NOAA's predicted smoothed sunspot number for the month of date_utc. Raises an error if the month is not in the file.
    rows = space_fetch('json/solar-cycle/predicted-solar-cycle.json', True)
    month_tag = date_utc.strftime('%Y-%m')
    for row in rows:
        if row['time-tag'] == month_tag:
            return int(round(float(row['predicted_ssn'])))
    raise ValueError('month not in the predicted solar cycle file')

def space_report(forecast_day, sender_callsign, request_callsign):
    # One-line space weather report. Day 0 is current conditions, days 1 and up come from NOAA's 27-day outlook.
    # Dates are UTC. If anything fails, the reply is SPACE WX UNAVAIL.
    try:
        day = int(forecast_day)
        date_utc = datetime.datetime.now(datetime.timezone.utc).date() + datetime.timedelta(days=day)
        if day == 0:
            scales = space_fetch('products/noaa-scales.json', True)['0']
            flux = space_latest_flux()
            ssn_part = []
            try:
                ssn_part = ['SSN%d' % space_predicted_ssn(date_utc)]
            except Exception as e:
                print(e)
            parts = ['SPACE', date_utc.isoformat(), 'OBS', 'SFI%d' % flux] + ssn_part + ['K%.1f' % space_latest_kp(),
                     'G' + str(scales['G']['Scale']), 'S' + str(scales['S']['Scale']), 'R' + str(scales['R']['Scale'])]
        else:
            outlook = space_outlook_table().get(date_utc)
            if outlook is None:
                raise ValueError('date not in the 27-day outlook')
            parts = ['SPACE', date_utc.isoformat(), 'FCST', 'SFI%d' % outlook[0], 'KMAX%d' % outlook[1]]
            try:
                forecast = space_fetch('products/noaa-scales.json', True)
                for key in ('1', '2', '3'):
                    if forecast[key]['DateStamp'] == date_utc.isoformat() and forecast[key]['G']['Scale'] is not None:
                        parts.append('G' + str(forecast[key]['G']['Scale']))
                        break
            except Exception as e:
                print(e)
        report = ' '.join(parts)
    except Exception as e:
        print(e)
        report = 'SPACE WX UNAVAIL'
    print(sender_callsign + ': ' + request_callsign + ' MSG ' + report)
    return report

def nav_grid_center(grid):
    # Converts a 4, 6 or 8 character Maidenhead grid to the latitude and longitude of the CENTER of that square.
    grid = grid.strip().upper()
    if len(grid) not in (4, 6, 8):
        raise ValueError('bad grid length')
    lon = (ord(grid[0]) - ord('A')) * 20.0 - 180.0
    lat = (ord(grid[1]) - ord('A')) * 10.0 - 90.0
    lon += int(grid[2]) * 2.0
    lat += int(grid[3]) * 1.0
    lon_size = 2.0
    lat_size = 1.0
    if len(grid) >= 6:
        lon += (ord(grid[4]) - ord('A')) * (2.0 / 24.0)
        lat += (ord(grid[5]) - ord('A')) * (1.0 / 24.0)
        lon_size = 2.0 / 24.0
        lat_size = 1.0 / 24.0
    if len(grid) == 8:
        lon += int(grid[6]) * (lon_size / 10.0)
        lat += int(grid[7]) * (lat_size / 10.0)
        lon_size = lon_size / 10.0
        lat_size = lat_size / 10.0
    return lat + lat_size / 2.0, lon + lon_size / 2.0

def nav_find_places(text):
    # Finds up to two places in the text. A place is a Maidenhead grid or a decimal "lat, lon" pair.
    # Returns a list of (label, latitude, longitude).
    pattern = r'(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)|\b([A-Ra-r]{2}[0-9]{2}(?:[A-Xa-x]{2}(?:[0-9]{2})?)?)\b'
    places = []
    for match in re.finditer(pattern, text):
        if match.group(3):
            lat, lon = nav_grid_center(match.group(3))
            places.append((match.group(3).upper(), lat, lon))
        else:
            lat = float(match.group(1))
            lon = float(match.group(2))
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                places.append((match.group(1) + ',' + match.group(2), lat, lon))
        if len(places) == 2:
            break
    return places

def nav_distance_bearing(lat1, lon1, lat2, lon2):
    # Great-circle distance in kilometers and initial TRUE bearing in degrees from point 1 to point 2.
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    distance = 2 * 6371.0088 * math.asin(min(1.0, math.sqrt(a)))
    y = math.sin(dl) * math.cos(p2)
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    bearing = (math.degrees(math.atan2(y, x)) + 360.0) % 360.0
    return distance, bearing

def nav_report(request_text, default_grid, display_unit_type, sender_callsign, request_callsign):
    # One-line distance and bearing report. Works fully offline.
    # request_text is everything the sender typed after NAV?. One place means "from the server's default grid".
    try:
        places = nav_find_places(request_text)
        if len(places) == 0:
            report = 'NAV USE NAV? TO OR NAV? FROM TO'
        else:
            if len(places) == 1:
                lat, lon = nav_grid_center(default_grid)
                places.insert(0, (default_grid.upper(), lat, lon))
            start = places[0]
            end = places[1]
            distance_km, bearing = nav_distance_bearing(start[1], start[2], end[1], end[2])
            if display_unit_type == 'imperial':
                distance_text = str(int(round(distance_km * 0.621371))) + 'MI'
            else:
                distance_text = str(int(round(distance_km))) + 'KM'
            parts = ['NAV', start[0] + '>' + end[0], distance_text]
            if distance_km >= 0.5:
                parts.append('BRG%03dT' % (int(round(bearing)) % 360))
            report = ' '.join(parts)
    except Exception as e:
        print(e)
        report = 'NAV UNAVAIL'
    print(sender_callsign + ': ' + request_callsign + ' MSG ' + report)
    return report

def ant_report(request_text, display_unit_type, sender_callsign, request_callsign):
    # One-line antenna length report. Works fully offline.
    # Half-wave dipole total length in feet = 468 / MHz. Quarter-wave vertical in feet = 234 / MHz.
    try:
        match = re.search(r'\d+(?:\.\d+)?', request_text)
        frequency = float(match.group(0)) if match else 0.0
        if not 0.1 <= frequency <= 1300:
            report = 'ANT USE MHZ EX ANT? 14.078'
        else:
            dipole_feet = 468.0 / frequency
            vertical_feet = 234.0 / frequency
            if display_unit_type == 'imperial':
                dipole_text = '%.1fFT' % dipole_feet
                vertical_text = '%.1fFT' % vertical_feet
            else:
                dipole_text = '%.1fM' % (dipole_feet * 0.3048)
                vertical_text = '%.1fM' % (vertical_feet * 0.3048)
            report = 'ANT %sMHZ DIPOLE %s TOTAL VERT %s' % (match.group(0), dipole_text, vertical_text)
    except Exception as e:
        print(e)
        report = 'ANT UNAVAIL'
    print(sender_callsign + ': ' + request_callsign + ' MSG ' + report)
    return report

def print_time():
    t = time.localtime()
    current_time = time.strftime("%H:%M:%S", t)
    print()
    print(current_time)

def return_time():
    t = time.localtime()
    current_time = time.strftime("%H:%M:%S", t)
    return(current_time)

def return_date_and_time():
    t = time.localtime()
    current_date_and_time = time.strftime("%n%Y %b %d %H:%M:%S %t%n", t)
    return(current_date_and_time)

# Check for API key
if API_key == 'Your_API_key_Here':
    print('Please enter your openopenweathermap.org API key in script in User Definition Area.')

########################
# Connect to JS8Call

js8host="localhost"
js8port=2442

print("Connecting to JS8Call...")
start_net(js8host,js8port)
print("Connected.")
get_band_activity()

#######################
# Print my call and server connection status 

my_call = get_callsign()
print(my_call + ' Lantern WX v1.2 active. Listening for requests...')

# Text to trigger forecast transmission
wx_trigger = 'WX?'
wind_trigger = 'WIND?'
email_trigger = 'EMAIL?'
help_trigger = 'HELP?'
message_trigger = 'MSG'
brief_trigger = 'WXB?'
moon_trigger = 'MOON?'
sun_trigger = 'SUN?'
space_trigger = 'SPACE?'
nav_trigger = 'NAV?'
ant_trigger = 'ANT?'
# Initialize values and paths
request_grid = ''
transcript_file = 'transcript.txt'
# Set initial values of latitude and longitude to default settings
coords = mh.to_location(default_grid)
latitude = str(coords[0])
longitude = str(coords[1])

# Message Beacon Timers
previous_message_time_1 = time.time() 
previous_message_time_2 = time.time() 
previous_message_time_3 = time.time() 
previous_message_time_4 = time.time() 
previous_message_time_5 = time.time() 

# Mouse Click Simulator
xvar = 1
yvar = 1
previous_mouse_click_time = time.time()

if ENABLE_MOUSE_CLICK_SIMULATOR:
# Display alert screen
    pg.alert('Mouse Click Simulator: Click OK, then click the desired mouse click location on the screen.')
# Start listener for mouse clicks
    listener = mouse.Listener(on_click=on_click)
    listener.start()
    listener.join()
    
##################
# BEGIN RUNTIME SECTION
# Check if anything is in receive queue, if so, get json data
last=time.time()
while(True):
    time.sleep(0.1)
    if(not(rx_queue.empty())):
        with rx_lock:
            rx=rx_queue.get()
            f=open("rx.json","a")
            f.write(json.dumps(rx))
            f.write("\n")
            f.close()
# Check for a message directed to my callsign    
            if(rx['type']=="RX.DIRECTED" and my_call == rx['params']['TO']):
                directed_message_to_my_call = rx['params']['TEXT']
                directed_message_to_my_call = directed_message_to_my_call.encode('ascii', 'ignore').decode('ascii')
# Split the recieved directed message
                split_message = re.split(r'\s', directed_message_to_my_call)
# Remove colon from incoming request callsign
                request_call = split_message[0].strip(':')
# print incoming directed message time and text
                print_time()
                print(directed_message_to_my_call)
# Initialize coordinate_format as not a decimal lat, lon
                coordinate_format = False
# Iterate through split text 
                for i in range(1,4):
# START TRIGGERED RESPONSE SECTION
# Check for trigger keywords
                    if split_message[i] == wx_trigger or split_message[i] == wind_trigger or split_message[i] == email_trigger or split_message[i] == help_trigger or split_message[i] == message_trigger or split_message[i] == brief_trigger or split_message[i] == moon_trigger or split_message[i] == sun_trigger or split_message[i] == space_trigger:
# Run message function
                        if split_message[i] == message_trigger and MSG_EMAIL_NOTIFICATION:
                            try:
                                message_body = directed_message_to_my_call
                                with open(transcript_file, 'a') as file:
                                    file.write('\n')
                                    file.write(return_date_and_time())
                                    file.write(directed_message_to_my_call)
                                msg_email_notification(request_call, my_call, message_email_address, message_body, email_address, email_server, email_password)
                            except Exception as e:
                                print(e)
                            
# Run email function
                        if split_message[i] == email_trigger and ENABLE_EMAIL:
                            try:
                                recipient_email = split_message[i+1]
                                message_body = directed_message_to_my_call
                                with open(transcript_file, 'a') as file:
                                    file.write('\n')
                                    file.write(return_date_and_time())
                                    file.write(directed_message_to_my_call)
                                email_push(request_call, my_call, recipient_email, message_body, email_address, email_server, email_password)
                            except Exception as e:
                                print(e)
# Help file server
                        if split_message[i] == help_trigger:
                            try:
                                file_path = 'help.txt'
                                print('Help file sent to: ' + request_call)
                                with open(file_path) as f:
                                    help_txt = f.read()
                                    send_inbox_message(request_call, help_txt)
                                with open(transcript_file, 'a') as file:
                                    file.write('\n' + return_date_and_time())
                                    file.write(directed_message_to_my_call + '\n')
                                    file.write('Help file sent to ' + request_call)
                            except Exception as e:
                                print(e)
# Check for decimal lat and lon format
                        split_message[4] = split_message[4].strip(',')
                        if re.search(r'[0-9]*\.[0-9]*', split_message[4]) and re.search(r'[0-9]*\.[0-9]*', split_message[5]) and -90 < float(split_message[4]) < 90 and -180 < float(split_message[5]) < 180:
                            try:
                                latitude = split_message[4]
                                longitude = split_message[5]
                                request_day = split_message[6]
# Toggle coordinate_format to indicate decimal lat, lon status
                                coordinate_format = True
                            except Exception as e:
                                print(e)
                        else:
# Check for maidenhead grid format
                            try:
                                if re.search(r'[A-Ra-r][A-Ra-r][0-9][0-9]', split_message[4]):
                                    coords = mh.to_location(split_message[4])
                                    latitude = str(coords[0])
                                    longitude = str(coords[1])
                                    request_day = split_message[5]
                                else:
# if not, set lat and lon to default grid location
                                    coords = mh.to_location(default_grid)
                                    latitude = str(coords[0])
                                    longitude = str(coords[1])
                                    request_day = split_message[4]
                            except Exception as e:
                                print(e)
# Make sure request_day is between 0 and 5                        
                        try:
                            days = ['0', '1', '2', '3', '4', '5']
                            if request_day not in days:
                                request_day = 0
                            request_day = int(request_day)
                        except Exception as e:
                            print(e)
# Run wx function to print and send wx report
                        if split_message[i] == wx_trigger:
                            try:
                                with open(transcript_file, 'a') as file:
                                    file.write(return_date_and_time())
                                    file.write(directed_message_to_my_call)
                                openweathermap_wx_api_call(request_day, API_key, unit_type, my_call, request_call, latitude, longitude, coordinate_format)
                            except Exception as e:
                                print(e)
# Run wind function to print and send wind report
                        if split_message[i] == wind_trigger:
                            try:
                                with open(transcript_file, 'a') as file:
                                    file.write(return_date_and_time())
                                    file.write(directed_message_to_my_call)
                                openweathermap_wind_api_call(request_day, API_key, unit_type, my_call, request_call, latitude, longitude, coordinate_format)
                            except Exception as e:
                                print(e)

# Run brief function to send the one-line WXB report
                        if split_message[i] == brief_trigger:
                            try:
                                with open(transcript_file, 'a') as file:
                                    file.write(return_date_and_time())
                                    file.write(directed_message_to_my_call)
                                if coordinate_format:
                                    brief_label = latitude + ',' + longitude
                                elif re.search(r'[A-Ra-r][A-Ra-r][0-9][0-9]', split_message[4]):
                                    brief_label = split_message[4].upper()
                                else:
                                    brief_label = default_grid
                                brief_text = openweathermap_brief_api_call(request_day, API_key, unit_type, my_call, request_call, latitude, longitude, brief_label)
                                if brief_text:
                                    send_inbox_message(request_call, brief_text)
                                    with open(transcript_file, 'a') as file:
                                        file.write('\n' + my_call + ': ' + request_call + ' MSG ' + brief_text + '\n')
                            except Exception as e:
                                print(e)

# Run moon function to send the one-line MOON report
                        if split_message[i] == moon_trigger:
                            try:
                                with open(transcript_file, 'a') as file:
                                    file.write(return_date_and_time())
                                    file.write(directed_message_to_my_call)
                                if coordinate_format:
                                    moon_label = latitude + ',' + longitude
                                elif re.search(r'[A-Ra-r][A-Ra-r][0-9][0-9]', split_message[4]):
                                    moon_label = split_message[4].upper()
                                else:
                                    moon_label = default_grid
                                moon_text = moon_report(request_day, my_call, request_call, latitude, longitude, moon_label)
                                if moon_text:
                                    send_inbox_message(request_call, moon_text)
                                    with open(transcript_file, 'a') as file:
                                        file.write('\n' + my_call + ': ' + request_call + ' MSG ' + moon_text + '\n')
                            except Exception as e:
                                print(e)

# Run sun function to send the one-line SUN report
                        if split_message[i] == sun_trigger:
                            try:
                                with open(transcript_file, 'a') as file:
                                    file.write(return_date_and_time())
                                    file.write(directed_message_to_my_call)
                                if coordinate_format:
                                    sun_label = latitude + ',' + longitude
                                elif re.search(r'[A-Ra-r][A-Ra-r][0-9][0-9]', split_message[4]):
                                    sun_label = split_message[4].upper()
                                else:
                                    sun_label = default_grid
                                sun_text = sun_report(request_day, my_call, request_call, latitude, longitude, sun_label)
                                if sun_text:
                                    send_inbox_message(request_call, sun_text)
                                    with open(transcript_file, 'a') as file:
                                        file.write('\n' + my_call + ': ' + request_call + ' MSG ' + sun_text + '\n')
                            except Exception as e:
                                print(e)

# Run space function to send the one-line SPACE report
                        if split_message[i] == space_trigger:
                            try:
                                with open(transcript_file, 'a') as file:
                                    file.write(return_date_and_time())
                                    file.write(directed_message_to_my_call)
                                space_text = space_report(request_day, my_call, request_call)
                                send_inbox_message(request_call, space_text)
                                with open(transcript_file, 'a') as file:
                                    file.write('\n' + my_call + ': ' + request_call + ' MSG ' + space_text + '\n')
                            except Exception as e:
                                print(e)

# Run nav function to send the one-line NAV report
                        if split_message[i] == nav_trigger:
                            try:
                                with open(transcript_file, 'a') as file:
                                    file.write(return_date_and_time())
                                    file.write(directed_message_to_my_call)
                                nav_text = nav_report(directed_message_to_my_call.split(nav_trigger, 1)[-1], default_grid, unit_type, my_call, request_call)
                                send_inbox_message(request_call, nav_text)
                                with open(transcript_file, 'a') as file:
                                    file.write('\n' + my_call + ': ' + request_call + ' MSG ' + nav_text + '\n')
                            except Exception as e:
                                print(e)
# Run antenna function to send the one-line ANT report
                        if split_message[i] == ant_trigger:
                            try:
                                with open(transcript_file, 'a') as file:
                                    file.write(return_date_and_time())
                                    file.write(directed_message_to_my_call)
                                ant_text = ant_report(directed_message_to_my_call.split(ant_trigger, 1)[-1], unit_type, my_call, request_call)
                                send_inbox_message(request_call, ant_text)
                                with open(transcript_file, 'a') as file:
                                    file.write('\n' + my_call + ': ' + request_call + ' MSG ' + ant_text + '\n')
                            except Exception as e:
                                print(e)

# Check message beacon time and send if over period
    if ENABLE_MESSAGE_BEACON_1:
        if time.time() > (message_period_1 * 60) + previous_message_time_1:
            print()
            print(return_time())
            print('Sending Message 1', message_file_path_1)
            previous_message_time_1 = time.time()
            message_beacon(message_file_path_1)
    if ENABLE_MESSAGE_BEACON_2:
        if time.time() > (message_period_2 * 60) + previous_message_time_2:
            print()
            print(return_time())
            print('Sending Message 2', message_file_path_2)
            previous_message_time_2 = time.time()
            message_beacon(message_file_path_2)
    if ENABLE_MESSAGE_BEACON_3:
        if time.time() > (message_period_3 * 60) + previous_message_time_3:
            print()
            print(return_time())
            print('Sending Message 3', message_file_path_3)
            previous_message_time_3 = time.time()
            message_beacon(message_file_path_3)
    if ENABLE_MESSAGE_BEACON_4:
        if time.time() > (message_period_4 * 60) + previous_message_time_4:
            print()
            print(return_time())
            print('Sending Message 4', message_file_path_4)
            previous_message_time_4 = time.time()
            message_beacon(message_file_path_4)
    if ENABLE_MESSAGE_BEACON_5:
        if time.time() > (message_period_5 * 60) + previous_message_time_5:
            print()
            print(return_time())
            print('Sending Message 5', message_file_path_5)
            previous_message_time_5 = time.time()
            message_beacon(message_file_path_5)
    if ENABLE_MOUSE_CLICK_SIMULATOR:
        if time.time() > (mouse_click_period * 60) + previous_mouse_click_time:
            pg.click(xvar, yvar)
            t = time.localtime()
            current_time = time.strftime("%c", t)
            print()
            print('Mouse click at:', current_time)
            print('Next mouse click in '+ str(mouse_click_period) + ' minute(s).')
            previous_mouse_click_time = time.time()