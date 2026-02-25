def calculate_earnings_cents(start_time: int, end_time: int) -> int:
    duration_seconds = end_time - start_time #how long the recording was
    if duration_seconds < 0:
        return 0
    duration_minutes = duration_seconds // 60 # convert to minutes
    return (duration_minutes * 100) // 60  # minutes to cents


    