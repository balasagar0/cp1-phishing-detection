"""The eight demo cases TC-01 to TC-08. HAND-WRITTEN, NOT A TEST SET: never compute a rate from them and never train on them.
Before this file they lived only in PROJECT_STATE.md (15 Oct) and in the presets of tests/test_window_and_ids.py and the console.
The messages are the ones v2 was demonstrated with; each case is a /correlate request body (TC-03 is a call, which v2 cannot assess).
Used by tests/test_demo_cases.py, the console presets, scripts/preflight.py and scripts/benchmark.py."""
import copy

KYC_SMS = dict(channel="sms", text="Dear customer, your SBI account will be blocked today. Update your KYC now at http://sbi-kyc-update.top/verify-now.php or call 9876543210", identity="+91 98765 43210", time="0")
KYC_URL = dict(channel="url", text="http://sbi-kyc-update.top/verify-now.php", time="4")
KYC_EMAIL = dict(channel="email", text="Dear customer, your bank account has been suspended. Verify your password within 24 hours at http://sbi-kyc-update.top/verify-now.php or your account will be closed.", subject="Urgent: account suspended", time="12")

BENIGN = [dict(channel="sms", text="Hey, can we move our project meeting to 4 pm tomorrow? I will email you the notes and an article on planning.", identity="+91 90000 11111", time="0"),
          dict(channel="email", text="Thanks for confirming. I wrote up the notes from yesterday. The article I mentioned is at https://en.wikipedia.org/wiki/Project_management if you want to read it. Call me tomorrow if anything changes.", subject="Re: project meeting", time="6"),
          dict(channel="url", text="https://en.wikipedia.org/wiki/Project_management", time="10")]
WEAK = [dict(channel="sms", text="Hello, there is a problem with your delivery address. Update it at parcel-redelivery.info/confirm today", time="0"),
        dict(channel="url", text="http://parcel-redelivery.info/track?id=88213", time="7"),
        dict(channel="email", text="Hello, we could not deliver your parcel today because the address on the label is incomplete. Please confirm your address at http://parcel-redelivery.info/confirm so we can try again. Thank you.", subject="Delivery problem with your parcel", time="15")]
COURIER = [dict(channel="sms", text="Your package will arrive tomorrow between 10 and 2. Track it at https://www.fedex.com/fedextrack/?trknbr=123456789012", identity="FedEx", time="0"),
           dict(channel="email", text="Hi, your FedEx shipment 123456789012 is on its way and will arrive tomorrow. You can follow it at https://www.fedex.com/fedextrack/?trknbr=123456789012. Thanks for shipping with us.", subject="Your shipment is on the way", time="10")]
CALL = dict(channel="call", text="Caller said he was from the bank's KYC desk and asked for the OTP sent to my phone to stop the account being blocked.", identity="+91 98765 43210", time="0")


def retime(ev, times):
    out = copy.deepcopy(ev)
    for e, t in zip(out, times): e["time"] = str(t)
    return out


CASES = {
    "TC-01": {"name": "Phishing email alone", "events": [dict(KYC_EMAIL, time="0")]},
    "TC-02": {"name": "Smishing SMS alone", "events": [dict(KYC_SMS)]},
    "TC-03": {"name": "Voice call (not assessed: no voice detector)", "events": [dict(CALL)]},
    "TC-04": {"name": "SMS + URL + email on one domain, 12 min", "events": [dict(KYC_SMS), dict(KYC_URL), dict(KYC_EMAIL)]},
    "TC-05": {"name": "A colleague shares an article, 10 min", "events": copy.deepcopy(BENIGN)},
    "TC-06": {"name": "Weak parcel campaign, 15 min", "events": copy.deepcopy(WEAK)},
    "TC-07": {"name": "TC-06's messages, 3 days apart", "events": retime(WEAK, [0, 4320, 8640])},
    "TC-08": {"name": "Courier SMS + email sharing a tracking number", "events": copy.deepcopy(COURIER)},
}


def case(cid):
    """A deep copy of one case, so callers can change it freely."""
    return copy.deepcopy(CASES[cid])
