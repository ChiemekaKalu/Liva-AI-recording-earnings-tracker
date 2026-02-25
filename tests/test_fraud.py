import sys
import threading
import pytest

sys.path.insert(0, "src")

from store import store
from services.recording import end_recording
from services.balance import get_balance, withdraw

def T(offset_minutes: float) -> int: #convert minutes to seconds
    return int(offset_minutes * 60)

@pytest.fixture(autouse=True)
def reset_store():
    store.reset()

# Earnings Tests

def test_basic_earnings_90_minutes():
    credits = end_recording("r1", T(0), T(90), ["u1", "u2"])
    u1 = next(c for c in credits if c.user_id == "u1")
    assert u1.amount_cents == 150 
    assert u1.reason == "credited"
    
def test_exactly_one_hour_earns_100_cents():
    credits = end_recording("r1", T(0), T(60), ["u1"])
    assert credits[0].amount_cents == 100

def test_less_than_one_minute_earns_zero_cents():
    credits = end_recording("r1", T(0), T(0) + 45, ["u1"])
    assert credits[0].amount_cents == 0
    assert credits[0].reason == "credited"  

def test_end_before_start_raises_error():
    with pytest.raises(ValueError, match="end_time must be greater than start_time"):
        end_recording("r1", T(60), T(0), ["u1"])

def test_end_equals_start_raises_error():
    with pytest.raises(ValueError, match="end_time must be greater than start_time"):
        end_recording("r1", T(60), T(60), ["u1"])

# Fraud Tests

def test_fraud_zeros_out_fradulent_user():
    end_recording("r1", T(0), T(60), ["u1", "u2"])  
    credits = end_recording("r2", T(30), T(90), ["u1", "u3"])
    
    u1 = next(c for c in credits if c.user_id == "u1")
    u3 = next(c for c in credits if c.user_id == "u3")

    assert u1.reason == "fraud"
    assert u3.reason == "credited" 
    assert u1.amount_cents == 0    
    assert u3.amount_cents == 100

def test_fraud_retroactively_reverses_prior_earnings():
    end_recording("r1", T(0), T(60), ["u1"])
    assert get_balance("u1") == 100 

    end_recording("r2", T(30), T(90), ["u1"])
    assert get_balance("u1") == 0

def test_innocent_participant_paid_normally():
    end_recording("r1", T(0), T(60), ["u1", "u2"])
    end_recording("r2", T(60), T(120), ["u1", "u3"])
    assert get_balance("u2") == 100 #should be never touched

def test_no_fraud_touching_endpoints():
    end_recording("r1", T(0), T(60), ["u1"])
    credits = end_recording("r2", T(60), T(120), ["u1"])
    assert credits[0].reason == "credited"
    assert get_balance("u1") == 200


#In the interest of time, I didn't write too many tests here for this section since the logic is pretty straightforward. 
# However, some other tests that could be included here is: no fraud on sequential recordings, fraud on second recording ending first, fraud user with clean people, 

# Balance and Withdrawal Tests

def test_withdraw_reduces_balance():
    end_recording("r1", T(0), T(60), ["u1"])
    new_balance = withdraw("u1", 50)
    assert new_balance == 50
    assert get_balance("u1") == 50

def test_withdraw_full_balance():
    end_recording("r1", T(0), T(60), ["u1"])
    new_balance = withdraw("u1", 100)
    assert new_balance == 0
    assert get_balance("u1") == 0

def test_withdraw_more_than_balance():
    end_recording("r1", T(0), T(60), ["u1"])
    with pytest.raises(ValueError, match="Insufficient funds"):
        withdraw("u1", 150)

def test_withdraw_zero_amount():
    end_recording("r1", T(0), T(60), ["u1"])
    with pytest.raises(ValueError, match="Amount must be positive"):
        withdraw("u1", 0)

def test_withdraw_negative_amount():
    end_recording("r1", T(0), T(60), ["u1"])
    with pytest.raises(ValueError, match="Amount must be positive"):
        withdraw("u1", -50)

    
    
# Edge Cases

def test_duplicate_participants_are_deduped():
    credits = end_recording("r1", T(0), T(60), ["u1", "u1", "u2"])
    u1_entries = [c for c in credits if c.user_id == "u1"]
    assert len(u1_entries) == 1

def test_double_end_same_recording_raises():
    end_recording("r1", T(0), T(60), ["u1"])
    with pytest.raises(ValueError, match="Recording already ended"):
        end_recording("r1", T(0), T(60), ["u1"])

def test_user_created_on_first_encounter():
    credits = end_recording("r1", T(0), T(60), ["brand new user"])
    assert credits[0].user_id == "brand new user"
    assert credits[0].reason == "credited"


# Concurrency 

def test_concurrent_end_same_recording_only_one_succeeds():
    errors = []
    successes = []

    def try_end():
        try:
            successes.append(end_recording("r1", T(0), T(60), ["u1"]))
        except ValueError as e:
            errors.append(str(e))

    threads = [threading.Thread(target=try_end) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(successes) == 1
    assert len(errors) == 9
    assert all("already ended" in e for e in errors)
    assert get_balance("u1") == 100

def test_concurrent_withdrawals_dont_exceed_balance():
    end_recording("r1", T(0), T(60), ["u1"])
    assert get_balance("u1") == 100

    errors = []
    successes = []

    def try_withdraw():
        try:
            successes.append(withdraw("u1", 60))
        except ValueError as e:
            errors.append(str(e))

    threads = [threading.Thread(target=try_withdraw) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(successes) == 1 #only 1 60 cent withdrawal fits in 100 cents
    assert len(errors) == 9    #9 failed withdrawals
    assert all("Insufficient funds" in e for e in errors)
    assert get_balance("u1") == 40 #100 - 60 = 40