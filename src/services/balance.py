from store import store

def get_balance(user_id: str) -> int:
    user = store.get_user(user_id)
    if not user:
        raise ValueError("User not found")
    return user.balance_cents

def withdraw(user_id: str, amount_cents: int) -> int:
   if amount_cents <= 0:
       raise ValueError("Amount must be positive")
   
   with store.get_user_lock(user_id):
       user = store.get_user(user_id)  
       if not user:
           raise ValueError("User not found")
   
       if user.balance_cents < amount_cents:
           raise ValueError("Insufficient funds")
   
       user.balance_cents -= amount_cents
    
   return user.balance_cents    