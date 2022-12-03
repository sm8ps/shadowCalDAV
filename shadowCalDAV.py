#!/usr/bin/env python3
from caldav import DAVClient
from caldav.lib import error
from datetime import datetime , timedelta
import os

####
# Server information:
CALDAV_URL = "https://my.nextcloud.tld/remote.php/dav"
CALDAV_USER = "userName"
CALDAV_PASSWORD = "useAppPassword"
# Timezone of calender.
# Use None for local timezone.
TIMEZONE = None
# Which calendars? Pairs of "internal" and "external" (= shadow) calendars
CALENDARS = [ ( 'La Praula' , '_LaPraula_WEB' ) ]
# Treat all events or only the ones since the last run?
#TREAT_ALL_EVENTS = True
TREAT_ALL_EVENTS = False
# Summary text for events in external calendar, end with whitespace if desired!
# Start/end time/date will be added (see below).
BUSY_TEXT = 'BELEGT '
# Format code for all-day or date/time events, respectively in strftime syntax, cf.
# https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes
DATE_FORMAT = '%d.%m.'
DATETIME_FORMAT = '%d.%m. %H:%M'
# Separator between start and end date(-time), include whitespace if desired!
FROM_TO_SEPARATOR = ' - '
# Remove all events from shadow calendar and do a fresh sync?
# # RESET_SHADOW_CALENDAR = False
# # Must wait for https://github.com/nextcloud/server/pull/34375!
# Directory must exist with write-permissions for the user running this script.
RUN_DIR = "/var/lib/shadowCalDAV/"
####

# 0) Sanity check about access permissions of this script file.
scriptPermsGO = oct( os.stat( __file__ ).st_mode )[-2:]
# only continue if not readable by anyone else
assert scriptPermsGO == '00'

def debug( *args ) :
    # print( *args )
    pass

def datetimeText( dateTime , pre = False ) :
    '''
    format "true" datetime events differently from all-day events
    '''
    if isinstance( dateTime , datetime ) :
        return dateTime.strftime( DATETIME_FORMAT )
    else :
        # Why use pre? Because vevent.dtend specifies
        # the first moment (= day) *after* the event.
        date = dateTime - pre * timedelta( days = 1 )
        return date.strftime( DATE_FORMAT )

def treatCalendar( calPair ) :
    debug( "( calInt , calExt ) =" , calPair )
    calNameInt , calNameExt = calPair
    calExt = pri.calendar( calNameExt )
    # if RESET_SHADOW_CALENDAR :
        # # # not working yet
        # objsExt = calExt.objects()
        # for obj in objsExt :
            # obj.delete()
        # objsExt = calExt.objects()
    calInt = pri.calendar( calNameInt )
    # 2) Get sync token from file if possible.
    syncToken = None
    run_file = RUN_DIR + calNameInt
    # if not RESET_SHADOW_CALENDAR and not TREAT_ALL_EVENTS :
    if not TREAT_ALL_EVENTS :
        if os.path.exists( run_file ) :
            with open( run_file ) as f :
                try :
                    syncToken = f.read()
                except FileNotFoundError :
                    # no run file (yet)
                    syncToken = None
    # 3) Get events with sync token or all events.
    try :
        deletedObjects = False
        objsInt = calInt.objects( sync_token = syncToken , load_objects = True )
    except error.AuthorizationError :
        # unknown sync token
        objsInt = calInt.objects( load_objects = True )
        debug( "unknown sync token" )
    except error.ResponseError as err :
        if err.url == "HTTP/1.1 418 I'm a teapot" :
            # deleted objects
            # cf. https://github.com/python-caldav/caldav/issues/203
            deletedObjects = True
            objsInt = calInt.objects( load_objects = True )
            debug( "deleted objects in calInt" )
        else :
            raise err
    # copy (new) objects from calInt to calExt
    debug( "checking (new) objects in calInt" )
    for obj in objsInt :
        debug( obj.vobject_instance.vevent.summary.value )
        # if RESET_SHADOW_CALENDAR :
            # objCopy = obj.copy( keep_uid = True , new_parent = calExt )
            # objCopy.save()
            # debug( "... copied to empty calExt" )
        # else :
        if True :
            # 4) Copy event to external calendar, replacing its summary by
            # start/end date/time while keeping its UID. If an event with that
            # UID already exists update it accordingly.
            objVevent = obj.vobject_instance.vevent
            uidInt = objVevent.uid.value
            dtstartInt = datetimeText( objVevent.dtstart.value )
            dtendInt = datetimeText( objVevent.dtend.value , pre = True )
            try :
                uidObjExt = calExt.event_by_uid( uidInt )
                uidObjExt.vobject_instance = obj.vobject_instance
                summaryExt = BUSY_TEXT + dtstartInt + FROM_TO_SEPARATOR + dtendInt
                uidObjExt.vobject_instance.vevent.summary.value = summaryExt
                uidObjExt.save()
                debug( "... updated in calExt as" , summaryExt )
            except error.NotFoundError :
                objCopy = obj.copy( keep_uid = True , new_parent = calExt )
                summaryExt = BUSY_TEXT + dtstartInt + FROM_TO_SEPARATOR + dtendInt
                objCopy.vobject_instance.vevent.summary.value = summaryExt
                objCopy.save()
                debug( "... copied to calExt" )
    if deletedObjects or TREAT_ALL_EVENTS :
        # 5) In case of deleted objects, load all events from external calendar
        # and delete the superfluous ones.
        debug( "checking objects in calExt:" )
        objsExt = calExt.objects( load_objects = True )
        for obj in objsExt :
            debug( obj.vobject_instance.vevent.summary.value )
            uidExt = obj.vobject_instance.vevent.uid.value
            try :
                calInt.event_by_uid( uidExt )
                debug( "... exists in calInt" )
            except error.NotFoundError :
                obj.delete()
                debug( "... deleted from calExt" )
    # 6) Store new sync token.
    with open( run_file , 'w' ) as f :
        f.write( objsInt.sync_token )
    debug()

baseURL = CALDAV_URL + "/calendars/" + CALDAV_USER + "/"
with DAVClient( url = baseURL , username = CALDAV_USER , password = CALDAV_PASSWORD ) as dav_client :
    # 1) Connect to CalDAV root ("principal") on CalDAV (Nextcloud) server.
    try :
        pri = dav_client.principal()
    except error.PropfindError :
        debug( "server unavailable. aborting" )
        exit()
    for calPair in CALENDARS :
        treatCalendar( calPair )
