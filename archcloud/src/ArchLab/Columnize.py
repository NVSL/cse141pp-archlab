import math

def columnize(data, divider="|", headers=1):
    r = ""
    column_count = max(map(len, data))
    rows = [x + ([""] * (column_count - len(x))) for x in data]
    widths = [max(list(map(lambda x:len(str(x)), col))) for col in zip(*rows)]
    div = "{}".format(divider)
    for i, row in enumerate(rows):
        if headers is not None and headers == i:
            r += divider.join(map(lambda x: "-" * (x), widths )) + "\n"
        r += div.join((str(val).ljust(width) for val, width in zip(row, widths))) + "\n"
    return r

    

def format_time_delta(t):
    if isinstance(t, str):
        return t
    seconds = t.days * 24*60*60 + t.seconds
    minutes = math.floor(seconds/60)
    hours = math.floor(minutes/60)
    return f"{hours}:{minutes % 60:02}:{seconds%60:02}"

def test_format_time_delta():
    import datetime
    assert format_time_delta("hello") == "hello"
    assert format_time_delta(datetime.timedelta(seconds=34)) == "0:00:34"
    assert format_time_delta(datetime.timedelta(seconds=3)) ==  "0:00:03"
    assert format_time_delta(datetime.timedelta(seconds=34, minutes=35)) == "0:35:34"
    assert format_time_delta(datetime.timedelta(seconds=34, minutes=61)) == "1:01:34"
    assert format_time_delta(datetime.timedelta(days=1)) == "24:00:00"
