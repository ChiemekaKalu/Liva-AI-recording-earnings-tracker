from dataclasses import dataclass
from typing import Literal

from store import store
from models import Recording, UserInterval, EarningsEntry
from utils.intervals import find_overlap, insert_interval
from services.earnings import calculate_earnings_cents

@dataclass
class CreditResult:
    user_id: str
    amount_cents: int
    reason: Literal["credited", "fraud"]

def end_recording(recording_id: str, start_time: int, end_time: int, participant_ids: list[str],) -> list[CreditResult]:
    if end_time <= start_time:
        raise ValueError("end_time must be greater than start_time")
    
    participants = list(dict.fromkeys(participant_ids)) # <-- remove duplicates, but preserve order
    recording_lock = store.get_recording_lock(recording_id)
    with recording_lock:
        existing = store.get_recording(recording_id)
        if existing and existing.status == "ended":
            raise ValueError("Recording already ended")
        
        store.set_recording(Recording(
            id=recording_id,
            start_time=start_time,
            end_time=end_time,
            participants=participants,
            status="ended"
        ))
        
        candidate = UserInterval(
            start_time=start_time,
            end_time=end_time,
            recording_id=recording_id
        )

        earnings_cents = calculate_earnings_cents(start_time, end_time)
        results = []

        for user_id in participants:
            with store.get_user_lock(user_id):
                user = store.get_or_create_user(user_id)
                conflict = find_overlap(user.intervals, candidate)
                
                if conflict:
                    user.earnings_log.append(EarningsEntry(recording_id=recording_id, amount_cents=0))
                    insert_interval(user.intervals, candidate)
                    prior = next( 
                        (e for e in user.earnings_log if e.recording_id == conflict.recording_id and not e.reversed), None
                    )
                    if prior:
                        prior.reversed = True
                        user.balance_cents = max(0, user.balance_cents - prior.amount_cents)
                    results.append(CreditResult(user_id=user_id, amount_cents=0, reason="fraud"))
                else:
                    user.earnings_log.append(EarningsEntry(recording_id=recording_id, amount_cents=earnings_cents))
                    user.balance_cents += earnings_cents
                    insert_interval(user.intervals, candidate)
                    results.append(CreditResult(user_id=user_id, amount_cents=earnings_cents, reason="credited"))
        
    return results
    