from sortedcontainers import SortedKeyList
from models import UserInterval 

def _overlaps(a: UserInterval, b: UserInterval) -> bool:
    return a.start_time < b.end_time and b.start_time < a.end_time

def find_overlap(intervals: SortedKeyList, candidate: UserInterval) -> UserInterval | None:
    if not intervals:
        return None
    
    idx = intervals.bisect_left(candidate)

    #check right
    if idx < len(intervals) and _overlaps(intervals[idx], candidate):
        return intervals[idx]
    
    #check left
    if idx > 0 and _overlaps(intervals[idx - 1], candidate):
        return intervals[idx - 1]
    
    return None


def insert_interval(intervals: SortedKeyList, interval: UserInterval) -> None:
    intervals.add(interval)
    

