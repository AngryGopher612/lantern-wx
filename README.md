Lantern WX - A weather and sky almanac for JS8CALL
====================================

A weather and sky-data server for amateur radio. Operators send a short
directed message over JS8Call and the server replies with a report: 
full forecast, brief forecast in METAR style, sunrise/sunset, moonrise/moonset, or space weather.

This project is built on top of the JS8Call WX Server by skyl4rk (MIT
license). The original commands, behavior and defaults are kept, so people who
already know the original server can use this one the same way. See CREDITS
AND LICENSE at the bottom. Massive thank you to them for building the bones and making this project possible.

Goal of this project: Add functionality for preparedness minded individuals, and
over time, make it keep working when the internet does not (see ROADMAP).


DATA SOURCES
------------

  OpenWeatherMap    Forecasts (WX?, WIND?, WXB?). API key required (it's free!).
  US National Weather Service (api.weather.gov)
                    Active weather alerts for US locations. No key.
  NOAA Space Weather Prediction Center (services.swpc.noaa.gov)
                    Solar flux, K index, storm scales, 27-day outlook.
                    No key. The format of these files can change, which is
                    why SPACE? answers "SPACE WX UNAVAIL" instead of failing.
  Sun and moon      Calculated locally using published low-precision
                    astronomical formulas. No data source.
                    

WHAT IT DOES
------------

You send a directed JS8Call message to the server host's callsign. It parses the
request, gets the data, and replies all in JS8CALL.

Request format (works for every command below):

    <server host's CALLSIGN> <COMMAND> [GRID] [DAY]

  - GRID: a Maidenhead grid square, for example DM71 or DN71MH. A longer
    grid is a smaller square and gives better results.
  - DAY: 0 to 5. 0 is today (the default). 1 is tomorrow, and so on.
  - Everything after the command is optional. If you leave out the grid, the
    server uses its default grid, usually the server owners location. If you leave out the day, you get day 0.
    This is on purpose, so a beginner who sends just the command still gets an answer.

Examples:

    WA1ABC WXB? DN22HW 3
    WA1ABC MOON? DN15
    WA1ABC SUN? 40.21, -86.14 1
    WA1ABC SPACE?


COMMANDS
--------

Original commands (unchanged except where noted):

  WX?     Longer forecast for the requested place and day.
  WIND?   Wind forecast through the day.
  EMAIL?  Forward a message by email (needs the email settings filled in).
  MSG     Notifies the station operator by email (optional).

  Change from the original: pressure now appears in inHg when the server is
  set to imperial units (for example "press 30.15 inHg"). In metric mode it
  still shows hPa/mb.

Commands:

  WXB?    One-line weather brief (METAR-inspired, NOT an official METAR).
  MOON?   Moonrise, moonset, how much of the moon is illuminated, as well as moon phase name. (Off grid capable)
  SUN?    Sunrise and sunset. (Off grid capable)
  SPACE?  Space weather: solar flux, geomagnetic K index, NOAA storm scales.
  NAV?    Distance and compass bearing between two places.
  ANT?    Antenna length for a frequency (dipole and quarter-wave vertical).


WXB? - ONE-LINE WEATHER BRIEF
-----------------------------

Example reply:

    2026-10-19 EM85KQ 20008G13mph -RA OVC 55/35 A3015 RMK ADVISORY: FROST

Reading it left to right:

  2026-10-19       Date (UTC) of the forecast
  EM85KQ           The place you asked for (your grid, or lat,lon)
  20008G13mph      Wind. Direction 200 degrees, speed 8, gusting 13, in mph.
                   Direction is rounded to the nearest 10 degrees. If there
                   are no gusts, the "G" part is left off. In metric mode the
                   unit is "mps" (meters per second).
  -RA              Weather. "-" light, "+" heavy, no sign moderate.
                   Codes: TS thunderstorm, RA rain, DZ drizzle, SN snow,
                   RASN rain and snow, FZRA freezing rain, PL ice pellets,
                   FG fog, BR mist, HZ haze, FU smoke, DU dust.
                   Left out when nothing notable is forecast. The most
                   significant condition of the day is shown.
  OVC              Sky cover (average for the day): CLR clear (10% or less),
                   FEW, SCT scattered, BKN broken, OVC overcast (above 87%)
  55/35            High and low temperature for the day (F, or C in metric)
  A3015            Pressure. A3015 means 30.15 inHg (inches x 100).
                   In metric mode it appears as Q1021 (hPa).
  RMK ADVISORY: FROST
                   Remark: an active National Weather Service alert. Only
                   shown for day 0. Only one alert is shown, in the order
                   warning, then watch, then advisory. US locations only.

Notes:
  - Wind is the highest wind and highest gust forecast during that UTC day.
    Gust data from the weather service can look high compared with the
    sustained wind, so treat the gust as a worst case.
  - The date and the "day" are UTC, not local time.
  - If the weather service cannot be reached, no reply is sent and the error
    is printed on the server console.


MOON? - MOONRISE, MOONSET, ILLUMINATION
---------------------------------------

Example reply:

    2026-10-19 DM42 MOON R2032 S0502 UTC ILL58% WAXING GIBBOUS

  R2032 / S0502    Moonrise 20:32 and moonset 05:02, in UTC
  --               Shown instead of a time when the moon does not rise (or
                   set) on that UTC day. This happens about once a month.
  ILL58%           Percent of the moon's disc that is lit, at 12:00 UTC
  WAXING GIBBOUS   Phase name: NEW (under 3% lit), FULL (over 97% lit),
                   FIRST QUARTER / LAST QUARTER (46% to 54% lit), otherwise
                   WAXING or WANING with CRESCENT (under 50%) or GIBBOUS


SUN? - SUNRISE AND SUNSET
-------------------------

Example reply:

    2026-10-19 FN14JK SUN R1233 S2319 UTC

  R1233 / S2319    Sunrise 12:33 and sunset 23:19, in UTC

Near the poles, on days when the sun never rises or never sets, the reply
says "SUN UP ALL DAY" or "SUN DOWN ALL DAY" instead of times.

Because the times are UTC, for places far east or west of Greenwich the
sunrise and sunset of one local day can fall on different UTC dates.

MOON? and SUN? work completely offline. See OFFLINE CAPABILITY below.


SPACE? - SPACE WEATHER
----------------------

Space weather is retrieved from the Space Weather Prediction Center.

Day 0 is current conditions:

    SPACE 2026-10-19 OBS SFI137 SSN88 K0.3 G0 S0 R0

  OBS      Observed (current) data
  SFI137   Solar flux at 10.7 cm. Higher generally means better HF
           propagation on the higher bands.
  SSN      Sunspot number for VOACAP use.
  K0.3     Latest planetary K index (geomagnetic activity), 0 to 9
  G0 S0 R0 NOAA scales, 0 (none) to 5 (extreme): G geomagnetic storm,
           S solar radiation storm, R radio blackout

Days 1 to 5 are a forecast:

    SPACE 2026-10-22 FCST SFI100 KMAX4 G1

  FCST     Forecast
  SFI100   Predicted solar flux for that date
  KMAX4    Largest K index predicted for that date
  G1       Predicted geomagnetic storm level, only when NOAA's 3-day
           forecast covers that date

The forecast comes from NOAA's 27-day outlook, which is a rough guide only.
It is updated weekly and can be well off the actual readings. Use it as a
general heads-up, not a prediction.

If the data cannot be reached or understood, the reply is:

    SPACE WX UNAVAIL

NAV? - DISTANCE AND BEARING
---------------------------
 
Example reply:
 
    NAV EN35MH>FN31 1033MI BRG098T
 
  EN35MH>FN31   From the first place to the second
  1033MI        Distance over the ground by the shortest route (miles, or KM
                in metric mode)
  BRG098T       Direction to head from the first place toward the second, in
                degrees. 0 is north, 90 is east, 180 is south, 270 is west.
                The T means TRUE bearing, measured from true north. A
                magnetic compass will point somewhere different by the
                local magnetic declination.
 
How to ask:
 
    NAV? FN31             From the server's default grid to FN31
    NAV? EN35MH FN31      From EN35MH to FN31
    NAV? 44.5, -93.2 FN31 Coordinates work in either place
 
If you send no place the server replies with a short reminder of the format.
If both places are the same, only the distance (0) is shown.
 
Accuracy: distance is within about half a percent (the Earth is treated as a
perfect sphere). A grid square is treated as its center point, so a 4-character
grid can be off by tens of miles. Use a 6-character grid or coordinates when it
matters. Works with no internet.
 
 
ANT? - ANTENNA LENGTH
---------------------
 
Example reply:
 
    ANT 14.078MHZ DIPOLE 33.2FT TOTAL VERT 16.6FT
 
  14.078MHZ   The frequency you asked for, in MHz
  DIPOLE ... TOTAL
              Total length of a half-wave dipole wire, both sides together
              (each side is half of the number shown)
  VERT        Length of a quarter-wave vertical, used with radials of the same
              length
 
Ask with the frequency in MHz, for example ANT? 7.078. In metric mode the
lengths are in meters. The numbers come from the common rules of thumb
468 / MHz and 234 / MHz (feet). Treat them as a starting point: wire type,
height and nearby objects all move the real resonance, so trim with an SWR
meter or antenna analyzer if you have one. Works with no internet.

OFFLINE CAPABILITY
------------------

  Works with no internet at all:   MOON?   SUN?
  Needs the internet:              WX?   WIND?   WXB?   SPACE?

MOON? and SUN? calculate their answers on the server from the date and the
location. They do not use any web service, key or download. The only thing
they need is a computer clock with the correct date. (A JS8Call station
already needs an accurate clock to decode signals.)

Accuracy, as checked during development against the US Naval Observatory's
published times for several dates and locations (including Sydney, Anchorage,
and a place above the Arctic Circle):

  - Sunrise, sunset, moonrise and moonset matched to within about a minute.
  - Percent illuminated matched to within about 1%.
  - Moon phase timing (new and full) is within about 25 minutes.

Grid squares: a 4-character grid such as FN27 covers a large area (roughly 2
degrees by 1 degree), so rise and set times can be off by a few minutes
depending on where in the square you actually are. A 6-character grid such
as FN27AM is accurate to well under a minute. Depending on the version of the
maidenhead library, a grid may be converted to the corner of its square
instead of the center.


INSTALLATION
------------

Requirements:

  - Python 3
  - JS8Call, running, with its API enabled and the port matching the one in
    the script (the script uses localhost, port 2442)
  - Python modules: js8net (the JS8Call API module from the original
    project), requests, maidenhead, pynput, pyautogui. The new commands also
    use the standard "math" and "datetime" modules.
  - A free OpenWeatherMap API key (needed for WX?, WIND?, WXB?)

Setup:

  1. Put your API key and your default grid in the "User Definition Area" at
     the top of the script just like in the original by skyl4rk.
  2. Choose imperial or metric units there.
  3. Start JS8Call, then start the script.
  4. From another station, send the server a command, for example
     "<SERVER CALLSIGN> SPACE?". You can also have another station forward you a request from yourself.


KNOWN LIMITATIONS
-----------------

  - WX?, WIND?, WXB? and SPACE? have no fallback yet. If the internet or the
    service is down, they do not answer (or answer SPACE WX UNAVAIL).
  - The free OpenWeatherMap forecast only reaches 5 days, in 3-hour steps.
  - "Days" and dates are UTC.
  - Requests are parsed by position, like the original, so keep the command
    first, then the optional grid or coordinates, then the optional day.
  - Daily highs and lows follow UTC dates, so for a place like the US
    Midwest the "day" is shifted by several hours from the local day.


ROADMAP
-------

Planned in stages. Each stage is built on top of the one before it:

  v1     The online-only server (this release), with the new commands above.
  v2     Stale-data fallback. If the internet is down, serve the last good
         data and clearly flag it as stale.
  v2.5   Rolling local archive, so a multi-day or rolling blackout still has
         recent real data. A free no-key forecast source (Open-Meteo, up to
         16 days ahead) is being considered to replace the 5-day limit.
  v3     A fully off-grid server that can also report from a local weather
         station when asked. If enough stations take part, reports could be
         combined into a mesoscale (regional) picture, which needs a shared
         report format, station location and elevation, and a consistent
         pressure convention.


CREDITS AND LICENSE
-------------------

Based on the JS8Call WX Server by skyl4rk: https://github.com/skyl4rk/JS8Call-WX_Server and uses the js8net library by Jeff Francis.
Developed with AI assistance.

This project is released under the MIT license. The license text, including
the original author's copyright notice and the copyright notice for these
changes, is in the file LICENSE.

Thanks to NOAA (Space Weather Prediction Center and National Weather
Service), OpenWeatherMap, and the US Naval Observatory, whose published times
were used to check the sun and moon calculations.

Maintained by: Christopher Colvin/KF0DRT
