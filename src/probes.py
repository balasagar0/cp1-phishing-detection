"""Hand-written probe inputs scored by the deployed models. NOT an evaluation: a few inputs chosen to expose weak spots."""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from predict import Detectors
from common import REPORTS
D = Detectors()
P = [("url", "legit", "https://www.paypal.com/signin"), ("url", "legit", "https://www.amazon.in/gp/your-account"), ("url", "legit", "https://accounts.google.com/signin"),
     ("url", "legit", "https://en.wikipedia.org/wiki/Phishing"), ("url", "legit", "https://docs.google.com/document/d/1AbCdEf/edit"),
     ("url", "malicious", "http://paypal-secure-login.verify-account.xyz/signin"), ("url", "malicious", "https://secure-appleid.apple.com.account-verify.ml/login"),
     ("url", "malicious", "http://sbi-kyc-update.top/verify-now.php"), ("url", "malicious", "http://192.168.4.7/login/index.php"),
     ("sms", "legit", "Your package will arrive tomorrow between 10 and 2. Track it at https://www.fedex.com/en-in/tracking.html"),
     ("sms", "legit", "Hey, can we move our project meeting to 4 pm tomorrow?"),
     ("sms", "malicious", "Dear customer, your SBI account will be blocked today. Update your KYC now at http://sbi-kyc-update.top/verify-now.php"),
     ("email", "legit", "Thanks for confirming. I wrote up the notes from yesterday. Call me tomorrow if anything changes."),
     ("email", "malicious", "Dear customer, your bank account has been suspended. Verify your password within 24 hours at http://sbi-kyc-update.top/verify-now.php")]
out = [{"channel": c, "truth": t, "input": x, "score": D.score(c, x)["score"]} for c, t, x in P]
(REPORTS / "probe_results.json").write_text(json.dumps(out, indent=1)); [print(f"{o['score']:.3f} {o['channel']:5s} {o['truth']:9s} {o['input'][:70]}") for o in out]
