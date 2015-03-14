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


### Example Output

```
t=2015-03-14T02:51:00 cpu=0.506431422302 mem=0.489591065804 s=1494 int=60
t=2015-03-14T02:52:00 cpu=0.492681923175 mem=0.495022286751 s=1506 int=60
```

Each record provides:
- `t` the timestamp for the (aggregate) data sample range
- `cpu` the averaged CPU load time for that sample range
- `mem` the averaged Memory load time for that sample range
- `s` the number of samples in the given range
- `int` the scale (seconds) of the given range


## Design Considerations

Recording of incoming data needs to be fast, as presumably it'll run at much higher volume. Reporting (i.e. querying) of the dataset should still be fast as possible, but this is a secondary priority.