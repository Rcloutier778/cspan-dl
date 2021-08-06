
#Series name to the ID used in SCHEDULE_SHEET
SERIES_NAME_TO_ID_DICT = {
'CSPAN': None,
'BookTV':70,
}


#CSPAN
SCHEDULE_SHEET = 'https://www.c-span.org/schedule/print/?date={date}' #YYYY-mm-dd

#BookTV
SERIES_SHEET = 'https://www.c-span.org/series/print/?date={date}&series={series}' #YYYY-mm-dd

def getURL(seriesName, **kwargs):
    if SERIES_NAME_TO_ID_DICT[seriesName] is None:
        return SCHEDULE_SHEET.format(**kwargs)
    return SERIES_SHEET.format(series=SERIES_NAME_TO_ID_DICT[seriesName], **kwargs)

