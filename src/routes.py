from flask import Blueprint, request, jsonify
from services.recording import end_recording
from services.balance import get_balance, withdraw

bp = Blueprint("api", __name__)

@bp.route("/recording/end", methods=["POST"])
def handle_end_recording():
    body = request.get_json()
    if not body:
        return jsonify({"error": "Request body required"}), 400
    
    required = ["recordingId", "startTime", "endTime", "participantIds"]
    if not all(k in body for k in required):
        return jsonify({"error": "Missing required fields"}), 400
    
    if not isinstance(body["participantsIds"], list):
        return jsonify({"error": "participantsIds must be an array"}), 400

    try:
        credits = end_recording(
            recording_id=body["recordingId"],
            start_time=int(body["startTime"]),
            end_time=int(body["endTime"]),
            participant_ids=body["participantsIds"]
        )
        return jsonify({
            "recordingId": body["recordingId"],
            "credits": [
                {
                    "userId": c.user_id,
                    "amountCents": c.amount_cents,
                    "amountDisplay": f"${c.amount_cents / 100:.2f}",
                    "reason": c.reason
                }
                for c in credits
            ],
        })
    except ValueError as e:
        status = 409 if "already ended" in str(e) else 400 #409 is a conflict since the recording exists and is already ended
        return jsonify({"error": str(e)}), status
    
    
@bp.route("/balance/<user_id>", methods=["GET"])
def handle_get_balance(user_id):                                    
    try:
        balance = get_balance(user_id)
        return jsonify({
            "userId": user_id,
            "balanceCents": balance,
            "balanceDisplay": f"${balance / 100:.2f}"
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 404 #not found since the user doesn't exist              

@bp.route("/withdraw", methods=["POST"])
def handle_withdraw():
    body = request.get_json()
    if not body or "userId" not in body or "amountCents" not in body:
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        new_balance = withdraw(body["userId"], int(body["amountCents"]))
        return jsonify({"success": True, "newBalanceCents": new_balance}) 

    except ValueError as e:
        status = 400 if "Insufficient" in str(e) or "positive" in str(e) else 404
        return jsonify({"success": False, "error": str(e)}), status
            
    