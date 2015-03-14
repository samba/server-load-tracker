# ServerTrack

Performance tracking service, with data residing solely in server memory, employing a threaded model for concurrent request handling.

## Design Considerations

Recording of incoming data needs to be fast, as presumably it'll run at much higher volume. Reporting (i.e. querying) of the dataset should still be fast as possible, but this is a secondary priority.


This provides a simplistic RESTful HTTP interface for both recording (data in-take) and reporting. As such, individual hosts (reporting their performance) are treated as "collections" in the REST sense. Individual samples are _not_ accessible through the REST API though.

## Recording 

```http
POST /perf/{hostname}/

cpuload={cpuload}&memload={memload}
```

Parameters
- `cpuload` a float/double, representing CPU load percentage
- `memload` a float/double, representing Memory load percentage

Append a record to the performance history of the given hostname.



## Reporting

```http
GET /perf/{hostname}/{mode}
```

Mode is required and can be one of:
- `last_hour`: list average load values by minute for the preceding 60 minutes 
- `last_day`: list average load values by hour for the preceding 24 hours
- `last_minute`: as above, values by seconds for preceding 60 seconds (for testing)

The response is given in JSON.

### Example Output

```
[   
    {"memload": 83.47, "cpuload": 4.23, "interval": 1, "samples": 59, "time": "2015-03-14T04:16:11"}, 
    {"memload": 85.21, "cpuload": 4.35, "interval": 1, "samples": 58, "time": "2015-03-14T04:16:12"}, 
    ...
]
```

The values `memload` and `cpuload` represent averages for the given time intervals.



