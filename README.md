# ServerTrack

Performance tracking host.
- No persistent storage (only in-memory)
- Threading to support concurrent access to all endpoints.

## Recording 

```http
POST /perf/{hostname}/

cpuload=1.00&memload=1.00
```

Parameters
- `cpuload` a float/double, representing CPU load percentage
- `memload` a float/double, representing Memory load percentage

Append a record to the performance history of the given hostname.



## Reporting

```http
GET /perf/{hostname}/{mode}
```

Mode can be one of:
- `last_hour`: list average load values by minute for the preceding 60 minutes 
- `last_day`: list average load values by hour for the preceding 24 hours


## Design Considerations

Recording of incoming data needs to be fast, as presumably it'll run at much higher volume. Reporting (i.e. querying) of the dataset should still be fast as possible, but this is a secondary priority.