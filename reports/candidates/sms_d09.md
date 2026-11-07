# SMS by lure type (Phase 3.3, D-09 and D-16)

Written by `scripts/sms_lure_report.py` on 2026-11-02T12:25:47+05:30. **Hand-written, not a test set**: one or two messages per lure type, so each row is one message's result, not a rate. Alert score = 1 - P(ham), the score the API uses for SMS.

Phishing messages missed: 1 of 16 (S-H02). Legitimate messages flagged: 3 of 16 (S-L05, S-H05, S-H08).

| ID | Group | Lure or message type | Expected | Alert score | P(smishing) | Result |
|---|---|---|---|---|---|---|
| S-P01 | Standard | Bank block threat | Phishing | 100.0% | 99.9% | right |
| S-P02 | Standard | KYC expiry | Phishing | 100.0% | 100.0% | right |
| S-P03 | Standard | Utility disconnection | Phishing | 95.7% | 72.6% | right |
| S-P04 | Standard | Lucky draw | Phishing | 100.0% | 100.0% | right |
| S-P05 | Standard | Parcel fee | Phishing | 99.4% | 99.2% | right |
| S-P06 | Standard | UPI refund | Phishing | 95.0% | 90.4% | right |
| S-P07 | Standard | Tax refund | Phishing | 96.6% | 95.6% | right |
| S-P08 | Standard | Job scam | Phishing | 89.0% | 69.9% | right |
| S-P09 | Standard | SIM deactivation | Phishing | 97.1% | 94.0% | right |
| S-P10 | Standard | Reward points | Phishing | 99.3% | 98.8% | right |
| S-P11 | Standard | Fake e-challan | Phishing | 99.2% | 89.6% | right |
| S-P12 | Standard | Account lock | Phishing | 99.8% | 99.8% | right |
| S-H01 | Hard case | Callback lure (no link) | Phishing | 89.4% | 81.4% | right |
| S-H02 | Hard case | Address confirmation (no link) | Phishing | 39.7% | 17.1% | **wrong** |
| S-H03 | Hard case | Plausible statement link | Phishing | 95.6% | 92.2% | right |
| S-H04 | Hard case | Roman-script Hindi lure | Phishing | 99.6% | 99.1% | right |
| S-L01 | Standard | One-time password | Legitimate | 20.4% | 2.3% | right |
| S-L02 | Standard | Shipping update | Legitimate | 4.2% | 0.3% | right |
| S-L03 | Standard | Appointment reminder | Legitimate | 10.2% | 5.6% | right |
| S-L04 | Standard | Personal message | Legitimate | 19.4% | 0.0% | right |
| S-L05 | Standard | Credit alert | Legitimate | 78.8% | 75.2% | **wrong** |
| S-L06 | Standard | College notice | Legitimate | 3.6% | 2.1% | right |
| S-L07 | Standard | Receipt | Legitimate | 4.4% | 1.2% | right |
| S-L08 | Standard | Travel confirmation | Legitimate | 0.2% | 0.1% | right |
| S-L09 | Standard | Family message | Legitimate | 0.0% | 0.0% | right |
| S-L10 | Standard | Cab update | Legitimate | 10.4% | 0.0% | right |
| S-L11 | Standard | Interview reminder | Legitimate | 15.7% | 12.1% | right |
| S-L12 | Standard | Plan renewal | Legitimate | 6.3% | 0.2% | right |
| S-H05 | Hard case | Card use alert | Legitimate | 85.8% | 83.1% | **wrong** |
| S-H06 | Hard case | OTP with warning | Legitimate | 34.7% | 31.6% | right |
| S-H07 | Hard case | Fee deadline | Legitimate | 24.0% | 21.6% | right |
| S-H08 | Hard case | Bill due date | Legitimate | 85.1% | 16.1% | **wrong** |

## Data and decision

No SMS retrain. The brief allows one only with real smishing data whose source and licence can be checked. The SMS data v2 already uses (LSDST, 5,971 raw messages) is the Mishra and Soni 'SMS Phishing Dataset for Machine Learning and Pattern Recognition' (Mendeley Data, DOI 10.17632/f45bkkt8pr.1, CC BY 4.0): same row and class counts. A search for a public set of legitimate transactional SMS (bank alerts, bills), which is what D-16 needs, found none with a stated licence. So D-09 and D-16 stay open.

**Proposed: accept D-09 because** the fault it describes (phishing-style SMS missed: 1 of 12 caught on the old build) no longer shows on v2: the misses above are the only ones, and the honest held-out measure is smishing-vs-rest F1 in reports/sms_metrics.json. SMS-03 still fails on its legitimate half, which is D-16. The team decides.

**D-16 stays open.** Legitimate transactional SMS (bank alerts, bill reminders) are flagged because the training set has few of them. Fixing it needs real legitimate transactional SMS with a clear licence, or the team's own messages collected with consent (as for R2-10).
