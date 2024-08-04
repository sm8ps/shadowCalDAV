# shadowCalDAV

Synchronize calendar events to a shadow calendar
where the event summary is veiled, i.e. replaced by
start and end date/time only.

## USAGE

This script is intended to be called periodically,
e.g. by Cron, without any options.
It can be run from any machine, not necessarily
the Nextcloud server. Sync tokens are used to
efficiently handle the synchronization.

### CAUTION

The password for Nextcloud is stored in the script file!
As a minimal precaution it is advisable to create an
app password for this access.

Currently, only the event summary is replaced; 
any other data is copied from the original event.
This can easily be changed but I do not have any
appropriate use case at hand.

## FILE SYSTEM, USER

A persistent directory should exist with write-permissions
for the user running this script; e.g. /var/lib/shadowCalDAV/
(-> configuration variable RUN_DIR).
It is used to store a sync token in one file per calendar.

Permissions: this file should be accessible by
its owner only (file permissions 700)

User: a dedicated user with network access is advisable.

## PREREQUISITES

Python module caldav in version >=11
Install it via PIP for user running this script by
```$ sudo -u USER python3 -m pip install caldav```

## OPTIONS

CALDAV_URL, CALDAV_USER, CALDAV_PASSWORD for CalDAV (Nextcloud) server.

TIMEZONE should be specified as None in order to use local instead of universal time.

CALENDARS is a list of pairs of "internal" and "external" (= shadow) calendars.

TREAT_ALL_EVENTS can be used to override the sync token.

RESET_SHADOW_CALENDAR cannot be implemented yet. It should allow
to purge all events from the shadow calendar and do a fresh sync.

### Summary text

The summary will be replaced by a string in the form of
```<BUSY_TEXT><StartDateTime*><FROM_TO_SEPARATOR><EndDateTime*>```

BUSY_TEXT, FROM_TO_SEPARATOR are constant strings; add whitespace if desired.

DATE_FORMAT, DATETIME_FORMAT are format codes in 
[strftime syntax](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes).

## OVERVIEW

0) Sanity check about access permissions of this script file.
1) Connect to CalDAV root ("principal") on CalDAV (Nextcloud) server.

   For each calendar pair of internal and external calendar:
2) Get sync token from file if possible.
3) Load all new events from internal calendar as per sync token or all events.
   For each such event:
4) Copy event to external calendar, replacing its summary by
start/end date/time while keeping its UID. If an event with that
UID already exists update it accordingly.
5) In case of deleted objects, load all events from external calendar
and delete the superfluous ones.
   For each calendar pair:
6) Store new sync token.
